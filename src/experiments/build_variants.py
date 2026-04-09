"""Generate feature-pruned dataset variants for experiment preparation."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import Any

import pandas as pd
from scipy.stats import pearsonr

from src.config import settings
from src.data.utils import save_json
from src.logger import get_logger
from src.utils import load_latest_dataset

logger = get_logger(__name__)


def _resolve_label_columns(df: pd.DataFrame) -> list[str]:
    """Resolve known label columns available in the current dataset."""
    return [col for col in settings.variant_label_columns if col in df.columns]


def _resolve_feature_columns(df: pd.DataFrame, label_columns: list[str]) -> list[str]:
    """Resolve feature columns excluding identifier and labels."""
    excluded = {"repo_url", *label_columns}
    return [col for col in df.columns if col not in excluded]


def _dominance_ratio(series: pd.Series) -> float:
    """Return the most common value ratio for a series."""
    normalized_counts = series.value_counts(dropna=False, normalize=True)
    if normalized_counts.empty:
        return 0.0
    return float(normalized_counts.iloc[0])


def _build_correlation_pruning_result(
    df: pd.DataFrame,
    feature_columns: list[str],
    threshold: float,
    p_value_threshold: float,
) -> dict[str, Any]:
    """Build drop set based on pairwise correlation and significance."""
    numeric_df = df.loc[:, feature_columns].copy()
    bool_cols = numeric_df.select_dtypes(include=["bool", "boolean"]).columns
    if len(bool_cols) > 0:
        for col in bool_cols:
            numeric_df[col] = numeric_df[col].astype("Int8")
    numeric_df = numeric_df.apply(pd.to_numeric, errors="coerce")

    correlated_pairs: list[dict[str, Any]] = []
    for feature_a, feature_b in combinations(numeric_df.columns, 2):
        series_a = numeric_df[feature_a]
        series_b = numeric_df[feature_b]
        valid_mask = series_a.notna() & series_b.notna()
        valid_a = series_a[valid_mask]
        valid_b = series_b[valid_mask]

        if len(valid_a) < 2:
            logger.info(
                "Skipping pair %s/%s: not enough valid samples (%s)",
                feature_a,
                feature_b,
                len(valid_a),
            )
            continue

        if valid_a.nunique(dropna=False) < 2 or valid_b.nunique(dropna=False) < 2:
            logger.info(
                "Skipping pair %s/%s: not enough unique values"
                "(feature_a unique: %s, feature_b unique: %s)",
                feature_a,
                feature_b,
                valid_a.nunique(dropna=False),
                valid_b.nunique(dropna=False),
            )
            continue

        corr_value, p_value = pearsonr(
            valid_a,
            valid_b,
        )

        if abs(corr_value) >= threshold and p_value < p_value_threshold:
            correlated_pairs.append(
                {
                    "feature_a": feature_a,
                    "feature_b": feature_b,
                    "correlation": float(corr_value),
                    "p_value": float(p_value),
                }
            )

    sorted_pairs = sorted(
        correlated_pairs,
        key=lambda pair: abs(pair["correlation"]),
        reverse=True,
    )
    pair_frequency: dict[str, int] = defaultdict(int)
    for pair in sorted_pairs:
        pair_frequency[pair["feature_a"]] += 1
        pair_frequency[pair["feature_b"]] += 1

    dropped_features: set[str] = set()
    dropped_feature_details: dict[str, list[dict[str, Any]]] = {}
    for pair in sorted_pairs:
        feature_a = pair["feature_a"]
        feature_b = pair["feature_b"]
        if feature_a in dropped_features or feature_b in dropped_features:
            continue

        freq_a = pair_frequency[feature_a]
        freq_b = pair_frequency[feature_b]
        if freq_a < freq_b:
            drop_feature, keep_feature = feature_a, feature_b
            drop_reason = "lower_pair_frequency"
        elif freq_b < freq_a:
            drop_feature, keep_feature = feature_b, feature_a
            drop_reason = "lower_pair_frequency"
        else:
            drop_feature, keep_feature = feature_b, feature_a
            drop_reason = "pair_frequency_tie_break"

        dropped_features.add(drop_feature)
        dropped_feature_details[drop_feature] = [
            {
                "kept_feature": keep_feature,
                "dropped_pair_frequency": pair_frequency[drop_feature],
                "kept_pair_frequency": pair_frequency[keep_feature],
                "correlation": round(pair["correlation"], 6),
                "p_value": round(pair["p_value"], 8),
                "threshold": threshold,
                "drop_reason": drop_reason,
            }
        ]

    return {
        "dropped_features": sorted(dropped_features),
        "dropped_feature_details": dropped_feature_details,
        "correlation_pairs_considered": len(sorted_pairs),
        "threshold": threshold,
        "p_value_threshold": p_value_threshold,
    }


def _build_dominance_pruning_result(
    df: pd.DataFrame,
    feature_columns: list[str],
    threshold: float,
) -> dict[str, Any]:
    """Build drop set based on the dominance-ratio criterion."""
    dropped_feature_details: dict[str, list[dict[str, Any]]] = {}
    dropped_features: list[str] = []

    for feature in feature_columns:
        dominance = _dominance_ratio(df[feature])
        if dominance > threshold:
            dropped_features.append(feature)
            dropped_feature_details[feature] = [
                {
                    "dominance_ratio": round(dominance, 6),
                    "threshold": threshold,
                    "drop_reason": "dominance_ratio_above_threshold",
                }
            ]

    return {
        "dropped_features": sorted(dropped_features),
        "dropped_feature_details": dropped_feature_details,
        "threshold": threshold,
    }


def _build_manual_selected_pruning_result(df: pd.DataFrame) -> dict[str, Any]:
    """Build drop set based on manually selected features."""
    dropped_features = [
        feature
        for feature in settings.variant_low_variance_selected_features
        if feature in df
    ]
    dropped_feature_details = {
        feature: [
            {
                "drop_reason": "manually_selected_feature",
            }
        ]
        for feature in dropped_features
    }

    return {
        "dropped_features": sorted(dropped_features),
        "dropped_feature_details": dropped_feature_details,
    }


def _save_variant(
    source_df: pd.DataFrame,
    source_manifest: dict[str, Any],
    source_version_dir: Path,
    variant_root: Path,
    variant_name: str,
    label_columns: list[str],
    method: str,
    method_parameters: dict[str, Any],
    dropped_features: list[str],
    dropped_feature_details: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Save one dataset variant and its manifest."""
    dropped_features = sorted(
        [feature for feature in dropped_features if feature in source_df]
    )
    variant_df = source_df.drop(columns=dropped_features, errors="ignore")

    variant_dir = variant_root / variant_name
    variant_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = variant_dir / "dataset.csv"
    manifest_path = variant_dir / "variant_manifest.json"
    variant_df.to_csv(dataset_path, index=False)

    feature_columns_after = _resolve_feature_columns(variant_df, label_columns)
    manifest_data: dict[str, Any] = {
        "variant": variant_name,
        "created_at": datetime.now(UTC).isoformat(),
        "source_dataset_version": source_manifest.get(
            "version",
            source_version_dir.name.removeprefix("v"),
        ),
        "source_dataset_path": str(source_version_dir / "dataset.csv"),
        "source_dataset_checksum": source_manifest.get("checksum"),
        "rows": len(variant_df),
        "total_columns": len(variant_df.columns),
        "feature_count": len(feature_columns_after),
        "label_columns": label_columns,
        "id_column": "repo_url",
        "method": method,
        "method_parameters": method_parameters,
        "dropped_features": dropped_features,
        "dropped_feature_count": len(dropped_features),
        "dropped_feature_details": dropped_feature_details or {},
    }

    save_json(manifest_data, manifest_path)
    logger.info(
        "Saved variant '%s' with %s dropped features: %s",
        variant_name,
        len(dropped_features),
        dataset_path,
    )

    return {
        "variant": variant_name,
        "rows": len(variant_df),
        "total_columns": len(variant_df.columns),
        "feature_count": len(feature_columns_after),
        "dropped_feature_count": len(dropped_features),
        "dropped_features": dropped_features,
        "dataset_path": str(dataset_path),
        "manifest_path": str(manifest_path),
    }


def build_variants(
    data_dir: Path | str | None = None,
):
    """Generate and save dataset variants for experiment preparation."""
    if data_dir is None:
        data_dir = settings.dataset_output_dir

    data_dir = Path(data_dir)

    source_df, source_manifest, source_version_dir = load_latest_dataset(
        data_dir=data_dir
    )

    label_columns = _resolve_label_columns(source_df)
    feature_columns = _resolve_feature_columns(source_df, label_columns)
    variant_root = source_version_dir / "variants"
    variant_root.mkdir(parents=True, exist_ok=True)

    logger.info("Generating variants from %s", source_version_dir / "dataset.csv")
    logger.info(
        "Rows: %s | Features: %s | Labels: %s",
        len(source_df),
        len(feature_columns),
        len(label_columns),
    )

    variant_summaries: list[dict[str, Any]] = []

    variant_summaries.append(
        _save_variant(
            source_df=source_df,
            source_manifest=source_manifest,
            source_version_dir=source_version_dir,
            variant_root=variant_root,
            variant_name="original",
            label_columns=label_columns,
            dropped_features=[],
            method="identity",
            method_parameters={},
        )
    )

    for threshold in settings.variant_correlation_thresholds:
        correlation_result = _build_correlation_pruning_result(
            df=source_df,
            feature_columns=feature_columns,
            threshold=threshold,
            p_value_threshold=settings.variant_correlation_pvalue_threshold,
        )
        variant_name = f"corr_{int(threshold * 100):03d}"
        variant_summaries.append(
            _save_variant(
                source_df=source_df,
                source_manifest=source_manifest,
                source_version_dir=source_version_dir,
                variant_root=variant_root,
                variant_name=variant_name,
                label_columns=label_columns,
                dropped_features=correlation_result["dropped_features"],
                method="correlation_pruning",
                method_parameters={
                    "correlation_threshold": threshold,
                    "p_value_threshold": settings.variant_correlation_pvalue_threshold,
                },
                dropped_feature_details=correlation_result["dropped_feature_details"],
            )
        )

    manual_selected_result = _build_manual_selected_pruning_result(source_df)
    variant_summaries.append(
        _save_variant(
            source_df=source_df,
            source_manifest=source_manifest,
            source_version_dir=source_version_dir,
            variant_root=variant_root,
            variant_name="manual_selection",
            label_columns=label_columns,
            dropped_features=manual_selected_result["dropped_features"],
            method="expert_selected_pruning",
            method_parameters={
                "selected_features": list(
                    settings.variant_low_variance_selected_features
                ),
            },
            dropped_feature_details=manual_selected_result["dropped_feature_details"],
        )
    )

    dominance_result = _build_dominance_pruning_result(
        df=source_df,
        feature_columns=feature_columns,
        threshold=settings.variant_dominance_threshold,
    )
    dominance_variant_name = (
        f"dom_{int(settings.variant_dominance_threshold * 100):03d}"
    )
    variant_summaries.append(
        _save_variant(
            source_df=source_df,
            source_manifest=source_manifest,
            source_version_dir=source_version_dir,
            variant_root=variant_root,
            variant_name=dominance_variant_name,
            label_columns=label_columns,
            dropped_features=dominance_result["dropped_features"],
            method="dominance_ratio_pruning",
            method_parameters={
                "dominance_threshold": settings.variant_dominance_threshold
            },
            dropped_feature_details=dominance_result["dropped_feature_details"],
        )
    )

    variants_manifest: dict[str, Any] = {
        "created_at": datetime.now(UTC).isoformat(),
        "source_dataset_version": source_manifest.get(
            "version",
            source_version_dir.name.removeprefix("v"),
        ),
        "source_dataset_path": str(source_version_dir / "dataset.csv"),
        "settings": {
            "correlation_thresholds": list(settings.variant_correlation_thresholds),
            "correlation_p_value_threshold": (
                settings.variant_correlation_pvalue_threshold
            ),
            "dominance_threshold": settings.variant_dominance_threshold,
            "manually_selected_features": list(
                settings.variant_low_variance_selected_features
            ),
        },
        "variants": variant_summaries,
    }
    overview_df = pd.DataFrame(variant_summaries).sort_values("variant")
    overview_path = variant_root / "variant_overview.csv"
    overview_df.to_csv(overview_path, index=False)

    save_json(variants_manifest, variant_root / "variants_manifest.json")

    logger.info("=" * 60)
    logger.info("Variant generation complete")
    logger.info("Output directory: %s", variant_root)
    logger.info("Overview file: %s", overview_path)
    logger.info("=" * 60)


if __name__ == "__main__":
    build_variants()
