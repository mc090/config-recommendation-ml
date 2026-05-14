"""Metrics utilities for CV-based training."""

from collections.abc import Callable
from typing import Any

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    make_scorer,
    precision_score,
    recall_score,
)

from src.config import settings
from src.experiments.training.enums import TrainingMetric


def get_metric_keys() -> list[str]:
    """Return configured training metric keys."""
    return [metric.value for metric in settings.training_metrics]


def _metric_scorer(metric_name: TrainingMetric | str) -> Callable[[Any], Any]:
    """Build scorer object for one supported metric key."""
    metric = TrainingMetric(metric_name)
    match metric:
        case TrainingMetric.ACCURACY:
            return make_scorer(accuracy_score)
        case TrainingMetric.BALANCED_ACCURACY:
            return make_scorer(balanced_accuracy_score)
        case TrainingMetric.PRECISION_MACRO:
            return make_scorer(precision_score, average="macro", zero_division=0)
        case TrainingMetric.PRECISION_MICRO:
            return make_scorer(precision_score, average="micro", zero_division=0)
        case TrainingMetric.PRECISION_WEIGHTED:
            return make_scorer(precision_score, average="weighted", zero_division=0)
        case TrainingMetric.RECALL_MACRO:
            return make_scorer(recall_score, average="macro", zero_division=0)
        case TrainingMetric.RECALL_MICRO:
            return make_scorer(recall_score, average="micro", zero_division=0)
        case TrainingMetric.RECALL_WEIGHTED:
            return make_scorer(recall_score, average="weighted", zero_division=0)
        case TrainingMetric.F1_MACRO:
            return make_scorer(f1_score, average="macro", zero_division=0)
        case TrainingMetric.F1_MICRO:
            return make_scorer(f1_score, average="micro", zero_division=0)
        case TrainingMetric.F1_WEIGHTED:
            return make_scorer(f1_score, average="weighted", zero_division=0)
    raise ValueError(f"Unsupported metric key: {metric_name}")


def build_scoring() -> dict[str, Callable[[Any], Any]]:
    """Build scoring dict for GridSearchCV from configured metric keys."""
    return {metric: _metric_scorer(metric) for metric in get_metric_keys()}


def summarize_cv_metrics(cv_fold_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate fold metrics as mean and std for each variant/model pair."""
    metric_columns = get_metric_keys()
    grouped = cv_fold_df.groupby(["variant", "model_family"], as_index=True)[
        metric_columns
    ].agg(["mean", "std"])
    flattened_columns: list[str] = []
    for column in grouped.columns:
        if isinstance(column, tuple):
            flattened_columns.append("_".join(str(part) for part in column))
        else:
            flattened_columns.append(str(column))
    grouped = grouped.set_axis(flattened_columns, axis="columns")
    grouped = grouped.reset_index()
    return grouped


def extract_best_fold_metrics_rows(
    cv_results: dict[str, Any],
    *,
    best_index: int,
    variant: str,
    model_family: str,
    n_folds: int,
) -> list[dict[str, Any]]:
    """Extract per-fold metric rows for the best GridSearch candidate."""
    rows: list[dict[str, Any]] = []
    metrics = get_metric_keys()
    for fold_idx in range(n_folds):
        row: dict[str, Any] = {
            "variant": variant,
            "model_family": model_family,
            "fold": fold_idx,
        }
        for metric in metrics:
            row[metric] = float(
                cv_results[f"split{fold_idx}_test_{metric}"][best_index]
            )
        rows.append(row)
    return rows
