"""Dataset-oriented utility helpers used across pipeline and notebooks."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.logger import get_logger

logger = get_logger(__name__)


def load_latest_dataset(
    data_dir: Path | str = "data/processed",
) -> tuple[pd.DataFrame, dict[str, Any], Path]:
    """Load the latest versioned dataset with its manifest."""
    data_dir = Path(data_dir)
    versions = [file for file in data_dir.iterdir() if file.is_dir()]

    if not versions:
        raise FileNotFoundError(
            f"No processed dataset found in {data_dir}. Run 'dvc repro' first."
        )

    latest_version = sorted(versions, reverse=True)[0]
    dataset_path = latest_version / "dataset.csv"
    manifest_path = latest_version / "manifest.json"

    df = pd.read_csv(dataset_path)

    with open(manifest_path) as f:
        manifest = json.load(f)

    logger.debug(
        "DATASET | rows=%d version=%s created=%s commit=%s",
        len(df),
        manifest.get("version", "unknown"),
        manifest.get("created_at", "unknown"),
        manifest.get("git_commit", "unknown")[:8],
    )

    return df, manifest, latest_version


def cast_bool_features_to_int(
    df: pd.DataFrame, feature_columns: list[str]
) -> pd.DataFrame:
    """Cast boolean feature columns to integer type for sklearn compatibility."""
    for col in feature_columns:
        series = df[col]
        if pd.api.types.is_bool_dtype(series):
            df[col] = series.astype("Int8")
        else:
            df[col] = pd.to_numeric(series, errors="coerce")
    return df


def create_run_dir(output_root: Path) -> Path:
    """Create timestamped run directory."""
    run_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir
