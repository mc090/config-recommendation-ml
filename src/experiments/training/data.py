"""Dataset loading and matrix preparation for training runs."""

from pathlib import Path

import pandas as pd

from src.config import settings
from src.experiments.training.schemas import TrainingMatrices, VariantData
from src.utils import cast_bool_features_to_int, load_latest_dataset


def load_variant_dataset(
    variant_name: str,
    data_dir: Path | str | None = None,
) -> VariantData:
    """Load one variant dataset from the latest processed dataset version."""
    _, source_manifest, version_dir = load_latest_dataset(
        data_dir=data_dir or settings.dataset_output_dir
    )
    source_version = source_manifest.get("version", version_dir.name.removeprefix("v"))

    variant_dataset_path = version_dir / "variants" / variant_name / "dataset.csv"
    if not variant_dataset_path.exists():
        raise FileNotFoundError(
            f"Variant dataset not found: {variant_dataset_path}. "
            "Generate variants first with `python -m src.experiments.build_variants`."
        )

    df = pd.read_csv(variant_dataset_path)
    return VariantData(
        variant=variant_name,
        source_version=source_version,
        df=df,
    )


def prepare_training_matrices(
    df: pd.DataFrame,
    *,
    label_columns: list[str],
) -> TrainingMatrices:
    """Prepare numeric feature matrix and multiclass combination target."""
    missing_labels = [label for label in label_columns if label not in df.columns]
    if missing_labels:
        raise ValueError(f"Missing required label columns: {missing_labels}")

    all_label_columns = {
        label for label in settings.variant_label_columns if label in df.columns
    }
    feature_columns = [
        col for col in df.columns if col != "repo_url" and col not in all_label_columns
    ]
    if not feature_columns:
        raise ValueError(
            "No feature columns available after excluding id and all labels."
        )

    x = df.loc[:, feature_columns].copy()
    x = cast_bool_features_to_int(x, feature_columns)

    y = (
        df.loc[:, label_columns]
        .copy()
        .astype(int)  # Convert bool to int: True->1, False->0
        .astype(str)  # Convert int to str for concatenation
        .agg("".join, axis=1)
        .rename("label_combination")
    )

    return TrainingMatrices(
        x=x,
        y=y,
        feature_columns=feature_columns,
        target_name="label_combination",
    )
