"""Reusable helpers for notebook analysis."""

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd


def configure_notebook_plots(
    *,
    figsize: tuple[float, float] = (8, 6),
    font_size: int = 13,
    use_whitegrid: bool = False,
) -> None:
    """Apply common plotting defaults used in analysis notebooks."""
    plt.rcParams["figure.figsize"] = figsize
    plt.rcParams["font.size"] = font_size
    plt.rcParams["savefig.format"] = "pdf"
    plt.rcParams["savefig.bbox"] = "tight"
    plt.rcParams["savefig.dpi"] = 300

    if use_whitegrid:
        import seaborn as sns

        sns.set_style("whitegrid")


def select_training_run_dir(
    training_root: Path | str,
    run_id: str | None = None,
) -> tuple[Path, list[Path]]:
    """Resolve a training run directory, defaulting to the latest available run."""
    root = Path(training_root)
    run_dirs = sorted([path for path in root.iterdir() if path.is_dir()])
    if not run_dirs:
        raise FileNotFoundError(f"No training runs found in: {root}")

    selected_run_dir = run_dirs[-1] if run_id is None else root / run_id
    if not selected_run_dir.exists():
        raise FileNotFoundError(f"Run not found: {selected_run_dir}")

    return selected_run_dir, run_dirs


def load_training_run_artifacts(
    selected_run_dir: Path | str,
    fallback_refit_metric: str,
) -> tuple[pd.DataFrame, dict[str, Any], str, str]:
    """Load cv summary and config artifacts for one training run."""
    run_dir = Path(selected_run_dir)
    cv_summary_path = run_dir / "cv_summary.csv"
    run_config_path = run_dir / "run_config.json"

    if not cv_summary_path.exists():
        raise FileNotFoundError(f"Missing cv_summary.csv: {cv_summary_path}")
    if not run_config_path.exists():
        raise FileNotFoundError(f"Missing run_config.json: {run_config_path}")

    cv_summary = pd.read_csv(cv_summary_path)
    run_config = json.loads(run_config_path.read_text())

    refit_metric = run_config.get("settings", {}).get(
        "training_gridsearch_refit_metric",
        fallback_refit_metric,
    )
    refit_col = f"{refit_metric}_mean"
    if refit_col not in cv_summary.columns:
        raise ValueError(f"Refit metric column not found in cv_summary: {refit_col}")

    return cv_summary, run_config, refit_metric, refit_col


def select_variant_rows(
    cv_summary: pd.DataFrame,
    variant: str,
    refit_col: str,
) -> pd.DataFrame:
    """Filter and rank CV rows for one dataset variant."""
    variant_rows = (
        cv_summary.loc[cv_summary["variant"] == variant]
        .sort_values(refit_col, ascending=False)
        .reset_index(drop=True)
    )
    if variant_rows.empty:
        available_variants = sorted(cv_summary["variant"].dropna().unique().tolist())
        raise ValueError(
            f"Variant '{variant}' not found in cv_summary. "
            f"Available variants: {available_variants}"
        )
    return variant_rows


def best_per_model_family(
    variant_rows: pd.DataFrame,
    refit_col: str,
) -> pd.DataFrame:
    """Return one best row per model family, sorted by refit score."""
    ranked_rows = variant_rows.sort_values(refit_col, ascending=False)
    best_rows = ranked_rows.drop_duplicates(subset=["model_family"], keep="first")
    columns = ["model_family", refit_col]
    if "best_params_json" in best_rows.columns:
        columns.append("best_params_json")
    return best_rows.loc[:, columns].reset_index(drop=True)


def build_run_artifact_version(run_name: str, run_config: dict[str, Any]) -> str:
    """Build a run-specific artifact version string used across analysis notebooks."""
    dataset_version = str(run_config.get("dataset_version", "unknown")).replace(
        "/", "-"
    )
    return f"{run_name}_v{dataset_version}"


def print_dataset_schema(
    df: pd.DataFrame,
    label_cols: list[str],
) -> dict[str, Any]:
    """Analyze dataset schema and print summary information."""
    feature_cols = [
        col for col in df.columns if col != "repo_url" and col not in label_cols
    ]

    schema: dict[str, Any] = {
        "id_col": "repo_url",
        "label_cols": label_cols,
        "feature_cols": feature_cols,
        "total_columns": len(df.columns),
        "n_features": len(feature_cols),
        "n_labels": len(label_cols),
    }

    print("Dataset Schema:")
    print(f"  Total columns: {schema['total_columns']}")
    print(f"  Identifier: 1 ({schema['id_col']})")
    print(f"  Features: {schema['n_features']}")
    print(f"  Labels: {schema['n_labels']}")

    return schema
