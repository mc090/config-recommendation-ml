"""Utility functions for the config-recommendation-ml project."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


def save_config_snapshot(run_id: str) -> Path:
    """Save reproducible config snapshot alongside dataset.

    This allows future you (or reviewers) to know EXACTLY how the dataset was created.
    """
    from src.config import settings

    snapshot_path = settings.logs_dir / f"config_{run_id}.json"

    with open(snapshot_path, "w") as f:
        json.dump(
            {
                "run_id": run_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "config": settings.to_reproducible_dict(),
            },
            f,
            indent=2,
        )

    return snapshot_path


def load_latest_dataset(
    data_dir: Path | str = "data/processed",
) -> tuple[pd.DataFrame, dict[str, Any], Path]:
    """Load the latest versioned dataset with its manifest."""
    data_dir = Path(data_dir)
    versions = sorted([d for d in data_dir.iterdir() if d.is_dir()], reverse=True)

    if not versions:
        raise FileNotFoundError(
            f"No processed dataset found in {data_dir}. Run 'dvc repro' first."
        )

    latest_version = versions[0]
    dataset_path = latest_version / "dataset.csv"
    manifest_path = latest_version / "manifest.json"

    df = pd.read_csv(dataset_path)

    with open(manifest_path) as f:
        manifest = json.load(f)

    print(f"\nDataset loaded: {len(df)} records")
    print(f"  Version: {manifest.get('version', 'unknown')}")
    print(f"  Created: {manifest.get('created_at', 'unknown')}")
    print(f"  Git commit: {manifest.get('git_commit', 'unknown')[:8]}")

    return df, manifest, latest_version


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
