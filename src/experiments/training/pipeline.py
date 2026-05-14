"""End-to-end orchestration for model training experiments."""

import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import mlflow
import pandas as pd
from mlflow.tracking import MlflowClient
from sklearn.model_selection import GridSearchCV

from src.config import settings
from src.experiments.training.data import (
    load_variant_dataset,
    prepare_training_matrices,
)
from src.experiments.training.metrics import (
    build_scoring,
    extract_best_fold_metrics_rows,
    get_metric_keys,
    summarize_cv_metrics,
)
from src.experiments.training.models import build_model_spec
from src.experiments.training.splitters import build_cv_splits
from src.logger import get_logger
from src.utils import get_git_commit
from src.utils.data import save_csv, save_json
from src.utils.experiments import create_run_dir

logger = get_logger(__name__)


def _log_run_start(run_id: str, run_dir: Path) -> None:
    """Log top-level run metadata."""
    logger.info(
        "RUN %s | variants %d | models %d | cv %d | refit %s",
        run_id,
        len(settings.training_variant_names),
        len(settings.training_enabled_model_families),
        settings.training_cv_folds,
        settings.training_gridsearch_refit_metric.value,
    )
    logger.info("ARTIFACTS | directory %s", run_dir)


def _log_variant_start(
    variant: str, *, n_rows: int, n_features: int, n_classes: int
) -> None:
    """Log variant-level start summary."""
    logger.info(
        "VARIANT %-18s | rows %d | features %d | classes %d",
        variant,
        n_rows,
        n_features,
        n_classes,
    )


def _log_model_start(variant: str, model_family_name: str) -> None:
    """Log model-family start."""
    logger.info("  MODEL %-18s | variant %s", model_family_name, variant)


def _best_candidate_summary(
    cv_results: dict[str, Any], *, best_index: int, metric_name: str
) -> dict[str, float | int]:
    """Return concise best-candidate summary values for logging/reporting."""
    return {
        "n_candidates_tested": len(cv_results["params"]),
        "best_refit_mean": float(cv_results[f"mean_test_{metric_name}"][best_index]),
        "best_refit_std": float(cv_results[f"std_test_{metric_name}"][best_index]),
    }


def _build_cv_candidates_df(
    *,
    cv_results: dict[str, Any],
    variant: str,
    model_family: str,
    refit_metric: str,
) -> pd.DataFrame:
    """Build one row per tested GridSearch candidate with params and CV."""
    params_list: list[dict[str, Any]] = cv_results["params"]
    metric_keys = [
        metric
        for metric in get_metric_keys()
        if f"mean_test_{metric}" in cv_results and f"std_test_{metric}" in cv_results
    ]
    rows: list[dict[str, Any]] = []

    for candidate_index, params in enumerate(params_list):
        row: dict[str, Any] = {
            "variant": variant,
            "model_family": model_family,
            "candidate_index": candidate_index,
            "rank_refit": int(cv_results[f"rank_test_{refit_metric}"][candidate_index]),
            "params_json": json.dumps(params, sort_keys=True),
        }
        for metric in metric_keys:
            row[f"{metric}_mean"] = float(
                cv_results[f"mean_test_{metric}"][candidate_index]
            )
            row[f"{metric}_std"] = float(
                cv_results[f"std_test_{metric}"][candidate_index]
            )
        for param_name, param_value in params.items():
            row[param_name] = str(param_value)
        rows.append(row)
    return pd.DataFrame(rows)


def _build_hyperparam_impact_df(
    *,
    cv_candidates_df: pd.DataFrame,
    refit_metric: str,
) -> pd.DataFrame:
    """Aggregate candidate-level rows by each hyperparameter value."""
    metric_cols = {
        col
        for col in cv_candidates_df.columns
        if col.endswith("_mean") or col.endswith("_std")
    }
    fixed_cols = {
        "variant",
        "model_family",
        "candidate_index",
        "rank_refit",
        "params_json",
        *metric_cols,
    }
    param_cols = [
        col
        for col in cv_candidates_df.columns
        if col not in fixed_cols and cv_candidates_df[col].notna().any()
    ]
    refit_mean_col = f"{refit_metric}_mean"
    refit_std_col = f"{refit_metric}_std"
    impact_frames: list[pd.DataFrame] = []

    for param_col in param_cols:
        if cv_candidates_df[param_col].dropna().nunique() < 2:
            continue
        grouped = (
            cv_candidates_df.dropna(subset=[param_col])
            .groupby(["variant", "model_family", param_col], dropna=False)
            .agg(
                candidates_tested=("candidate_index", "count"),
                rank_refit_best=("rank_refit", "min"),
                refit_mean_avg=(refit_mean_col, "mean"),
                refit_mean_best=(refit_mean_col, "max"),
                refit_std_avg=(refit_std_col, "mean"),
            )
            .reset_index()
            .rename(columns={param_col: "param_value"})
        )
        grouped["param_name"] = param_col
        impact_frames.append(grouped)

    if not impact_frames:
        return pd.DataFrame(
            columns=[
                "variant",
                "model_family",
                "param_name",
                "param_value",
                "candidates_tested",
                "rank_refit_best",
                "refit_mean_avg",
                "refit_mean_best",
                "refit_std_avg",
            ]
        )
    return pd.concat(impact_frames, ignore_index=True)


def _log_model_complete(
    model_family_name: str,
    *,
    refit_metric: str,
    best_refit_mean: float,
    best_refit_std: float,
    n_candidates_tested: int,
    elapsed_seconds: float,
) -> None:
    """Log model-family completion summary."""
    logger.info(
        "        %-18s | best %s %.4f +/- %.4f | candidates %d | %.1fs",
        model_family_name,
        refit_metric,
        best_refit_mean,
        best_refit_std,
        n_candidates_tested,
        elapsed_seconds,
    )


def _log_variant_complete(variant: str, elapsed_seconds: float) -> None:
    """Log variant completion time."""
    logger.info("VARIANT %-16s | done in %.1fs", variant, elapsed_seconds)


def _log_run_complete(
    run_id: str, *, elapsed_seconds: float, cv_summary_path: Path, run_config_path: Path
) -> None:
    """Log run completion summary."""
    logger.info(
        "RUN %s | completed in %.1fs | artifacts %s and %s",
        run_id,
        elapsed_seconds,
        cv_summary_path,
        run_config_path,
    )


def run_training_experiment(
    data_dir: Path | str | None = None,
    output_dir: Path | str | None = None,
) -> Path:
    """Run full training workflow for configured variants and model families."""
    run_started_at = perf_counter()
    data_dir = data_dir or settings.dataset_output_dir

    output_root = Path(output_dir or settings.training_output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    run_dir = create_run_dir(output_root)
    run_id = run_dir.name
    git_commit = get_git_commit()
    _log_run_start(run_id, run_dir)

    mlflow.set_tracking_uri(settings.training_mlflow_tracking_uri)
    mlflow.set_experiment(settings.training_mlflow_experiment_name)

    all_cv_fold_rows: list[dict[str, Any]] = []
    summary_meta_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    timing_rows: list[dict[str, Any]] = []
    cv_candidates_frames: list[pd.DataFrame] = []
    hyperparam_impact_frames: list[pd.DataFrame] = []
    model_run_ids: list[str] = []

    source_version: str | None = None

    for variant in settings.training_variant_names:
        variant_started_at = perf_counter()
        variant_data = load_variant_dataset(variant, data_dir=data_dir)
        if source_version is None:
            source_version = variant_data.source_version

        matrices = prepare_training_matrices(
            variant_data.df,
            label_columns=settings.training_stratify_label_columns,
        )
        fold_splits, combination_counts = build_cv_splits(
            matrices.y,
            n_splits=settings.training_cv_folds,
        )
        _log_variant_start(
            variant,
            n_rows=matrices.x.shape[0],
            n_features=matrices.x.shape[1],
            n_classes=matrices.y.nunique(),
        )

        for model_family in settings.training_enabled_model_families:
            model_started_at = perf_counter()
            model_family_name = model_family.value
            _log_model_start(variant, model_family_name)
            model_spec = build_model_spec(model_family, n_features=matrices.x.shape[1])
            grid_search = GridSearchCV(
                estimator=model_spec.pipeline,
                param_grid=model_spec.param_grid,
                scoring=build_scoring(),
                refit=settings.training_gridsearch_refit_metric.value,
                cv=fold_splits,
                n_jobs=settings.training_gridsearch_n_jobs,
                return_train_score=False,
                error_score="raise",
            )
            grid_search.fit(matrices.x, matrices.y)

            cv_results = grid_search.cv_results_
            best_index = int(grid_search.best_index_)
            refit_metric = settings.training_gridsearch_refit_metric.value
            best_summary = _best_candidate_summary(
                cv_results, best_index=best_index, metric_name=refit_metric
            )
            n_candidates_tested = int(best_summary["n_candidates_tested"])
            best_refit_mean = float(best_summary["best_refit_mean"])
            best_refit_std = float(best_summary["best_refit_std"])
            cv_candidates_df = _build_cv_candidates_df(
                cv_results=cv_results,
                variant=variant,
                model_family=model_family_name,
                refit_metric=refit_metric,
            )
            cv_candidates_frames.append(cv_candidates_df)
            hyperparam_impact_df = _build_hyperparam_impact_df(
                cv_candidates_df=cv_candidates_df,
                refit_metric=refit_metric,
            )
            if not hyperparam_impact_df.empty:
                hyperparam_impact_frames.append(hyperparam_impact_df)
            fold_rows = extract_best_fold_metrics_rows(
                cv_results,
                best_index=best_index,
                variant=variant,
                model_family=model_family_name,
                n_folds=settings.training_cv_folds,
            )
            all_cv_fold_rows.extend(fold_rows)
            summary_meta_by_key[(variant, model_family_name)] = {
                "best_params_json": json.dumps(
                    grid_search.best_params_, sort_keys=True
                ),
                "n_candidates_tested": n_candidates_tested,
                "combination_counts_json": json.dumps(
                    combination_counts, sort_keys=True
                ),
            }

            with mlflow.start_run(run_name=f"{variant}-{model_family_name}") as run:
                model_run_ids.append(run.info.run_id)
                mlflow.set_tags(
                    {
                        "run_id": run_id,
                        "git_commit": git_commit,
                        "dataset_version": source_version or "unknown",
                    }
                )
                mlflow.log_param("variant", variant)
                mlflow.log_param("model_family", model_family_name)
                mlflow.log_param("cv_folds", settings.training_cv_folds)
                mlflow.log_param(
                    "refit_metric", settings.training_gridsearch_refit_metric.value
                )
                for key, value in grid_search.best_params_.items():
                    mlflow.log_param(f"best__{key}", str(value))
                for metric in get_metric_keys():
                    mlflow.log_metric(
                        f"best_{metric}_mean",
                        float(cv_results[f"mean_test_{metric}"][best_index]),
                    )
                    mlflow.log_metric(
                        f"best_{metric}_std",
                        float(cv_results[f"std_test_{metric}"][best_index]),
                    )
            model_elapsed_seconds = perf_counter() - model_started_at
            summary_meta_by_key[(variant, model_family_name)]["fit_elapsed_seconds"] = (
                model_elapsed_seconds
            )
            timing_rows.append(
                {
                    "scope": "model",
                    "variant": variant,
                    "model_family": model_family_name,
                    "elapsed_seconds": model_elapsed_seconds,
                    "n_rows": int(matrices.x.shape[0]),
                    "n_features": int(matrices.x.shape[1]),
                    "n_classes": int(matrices.y.nunique()),
                    "n_candidates_tested": n_candidates_tested,
                }
            )
            _log_model_complete(
                model_family_name,
                refit_metric=refit_metric,
                best_refit_mean=best_refit_mean,
                best_refit_std=best_refit_std,
                n_candidates_tested=n_candidates_tested,
                elapsed_seconds=model_elapsed_seconds,
            )
        variant_elapsed_seconds = perf_counter() - variant_started_at
        timing_rows.append(
            {
                "scope": "variant",
                "variant": variant,
                "model_family": None,
                "elapsed_seconds": variant_elapsed_seconds,
                "n_rows": int(matrices.x.shape[0]),
                "n_features": int(matrices.x.shape[1]),
                "n_classes": int(matrices.y.nunique()),
                "n_candidates_tested": None,
            }
        )
        _log_variant_complete(variant, variant_elapsed_seconds)

    cv_fold_df = pd.DataFrame(all_cv_fold_rows)
    cv_summary_df = summarize_cv_metrics(cv_fold_df)
    summary_meta_df = pd.DataFrame(
        [
            {
                "variant": variant,
                "model_family": model_family,
                **meta,
            }
            for (variant, model_family), meta in summary_meta_by_key.items()
        ]
    )
    cv_summary_df = cv_summary_df.merge(
        summary_meta_df,
        on=["variant", "model_family"],
        how="left",
        validate="one_to_one",
    )
    if (
        cv_summary_df[
            ["best_params_json", "n_candidates_tested", "combination_counts_json"]
        ]
        .isna()
        .any()
        .any()
    ):
        raise ValueError(
            "Missing summary metadata for one or more variant/model_family rows"
            " in cv_summary."
        )
    ranking_column = f"{settings.training_gridsearch_refit_metric.value}_mean"
    cv_summary_df = cv_summary_df.sort_values(
        ["variant", ranking_column], ascending=[True, False]
    ).reset_index(drop=True)
    save_csv(cv_summary_df, run_dir / "cv_summary.csv")
    cv_summary_path = run_dir / "cv_summary.csv"
    cv_candidates_path = run_dir / "cv_candidates.csv"
    cv_candidates_df = (
        pd.concat(cv_candidates_frames, ignore_index=True)
        if cv_candidates_frames
        else pd.DataFrame()
    )
    save_csv(cv_candidates_df, cv_candidates_path)
    hyperparam_impact_path = run_dir / "hyperparameter_impact.csv"
    hyperparam_impact_df = (
        pd.concat(hyperparam_impact_frames, ignore_index=True)
        if hyperparam_impact_frames
        else pd.DataFrame(
            columns=[
                "variant",
                "model_family",
                "param_name",
                "param_value",
                "candidates_tested",
                "rank_refit_best",
                "refit_mean_avg",
                "refit_mean_best",
                "refit_std_avg",
            ]
        )
    )
    save_csv(hyperparam_impact_df, hyperparam_impact_path)
    timing_df = pd.DataFrame(timing_rows)
    run_elapsed_seconds = perf_counter() - run_started_at
    timing_df = pd.concat(
        [
            timing_df,
            pd.DataFrame(
                [
                    {
                        "scope": "run",
                        "variant": None,
                        "model_family": None,
                        "elapsed_seconds": run_elapsed_seconds,
                        "n_rows": None,
                        "n_features": None,
                        "n_classes": None,
                        "n_candidates_tested": None,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    timing_path = run_dir / "timing_summary.csv"
    save_csv(timing_df, timing_path)

    run_config_payload: dict[str, Any] = {
        "created_at": datetime.now(UTC).isoformat(),
        "git_commit": git_commit,
        "dataset_version": source_version or "unknown",
        "variants": list(settings.training_variant_names),
        "cv_folds": settings.training_cv_folds,
        "settings": settings.to_reproducible_dict(),
    }
    run_config_path = run_dir / "run_config.json"
    save_json(run_config_payload, run_config_path)

    mlflow_client = MlflowClient()
    for model_run_id in model_run_ids:
        mlflow_client.log_artifact(model_run_id, str(cv_summary_path))
        mlflow_client.log_artifact(model_run_id, str(cv_candidates_path))
        mlflow_client.log_artifact(model_run_id, str(hyperparam_impact_path))
        mlflow_client.log_artifact(model_run_id, str(run_config_path))
        mlflow_client.log_artifact(model_run_id, str(timing_path))

    _log_run_complete(
        run_id,
        elapsed_seconds=run_elapsed_seconds,
        cv_summary_path=cv_summary_path,
        run_config_path=run_config_path,
    )
    return run_dir
