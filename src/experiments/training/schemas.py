"""Typed structures used by the training pipeline."""

from dataclasses import dataclass
from typing import Any

import pandas as pd
from sklearn.pipeline import Pipeline


@dataclass
class VariantData:
    """Resolved dataset variant and metadata required for training."""

    variant: str
    source_version: str
    df: pd.DataFrame


@dataclass
class TrainingMatrices:
    """Feature matrix, multiclass target, and metadata for one variant."""

    x: pd.DataFrame
    y: pd.Series
    feature_columns: list[str]
    target_name: str


@dataclass
class ModelSpec:
    """Container for one model pipeline and its parameter grid."""

    pipeline: Pipeline
    param_grid: dict[str, list[Any]]
