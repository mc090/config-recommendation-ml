"""Cross-validation split utilities for training experiments."""

from collections import Counter

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from src.config import settings


def validate_class_counts(
    class_labels: pd.Series,
    n_splits: int,
) -> dict[str, int]:
    """Fail fast when any class has fewer samples than CV folds."""
    counts = Counter(class_labels.tolist())
    too_rare = {key: count for key, count in counts.items() if count < n_splits}
    if too_rare:
        details = ", ".join(
            f"{combination}={count}" for combination, count in sorted(too_rare.items())
        )
        raise ValueError(
            "Cannot create stable stratified CV folds; some target classes have "
            f"fewer than {n_splits} samples: {details}"
        )
    return dict(sorted(counts.items()))


def build_cv_splits(
    class_labels: pd.Series,
    *,
    n_splits: int,
) -> tuple[list[tuple[np.ndarray, np.ndarray]], dict[str, int]]:
    """Build sklearn-ready deterministic stratified CV splits."""
    class_counts = validate_class_counts(class_labels, n_splits)

    splitter = StratifiedKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=settings.random_seed,
    )

    dummy_x = np.zeros(len(class_labels))
    fold_splits = list(splitter.split(dummy_x, class_labels))

    return fold_splits, class_counts
