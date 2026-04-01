"""Build final dataset."""

import hashlib
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import settings
from src.data.utils import load_json, save_json
from src.logger import get_logger

logger = get_logger(__name__)


def _get_next_version(output_dir: Path) -> str:
    """Determine the next dataset version."""
    provided_version = settings.dataset_version

    if provided_version and not re.match(r"^\d+\.\d+\.\d+$", provided_version):
        raise ValueError(
            f"Invalid version format: '{provided_version}'. "
            "Expected semantic version (e.g., '1.0.0')"
        )

    version_pattern = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
    existing_versions: set[tuple[int, int, int]] = set()

    if output_dir.exists():
        for item in output_dir.iterdir():
            if item.is_dir():
                match = version_pattern.match(item.name)
                if match:
                    major, minor, patch = map(int, match.groups())
                    existing_versions.add((major, minor, patch))

    if not provided_version:
        if not existing_versions:
            return "1.0.0"

        latest = max(existing_versions)
        return f"{latest[0]}.{latest[1]}.{latest[2] + 1}"

    provided = tuple(map(int, provided_version.split(".")))

    if provided not in existing_versions:
        return provided_version

    major, minor, patch = provided
    while (major, minor, patch) in existing_versions:
        patch += 1
    next_version = f"{major}.{minor}.{patch}"
    return next_version


def _get_git_commit() -> str:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        logger.warning("Could not retrieve git commit hash")
        return "unknown"


def _compute_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return f"sha256:{sha256.hexdigest()}"


def build_dataset(
    input_path: Path | None = None,
    output_dir: Path | None = None,
) -> None:
    """Build final dataset."""
    input_path = input_path or settings.computed_features_path
    output_dir = output_dir or settings.dataset_output_dir

    version = _get_next_version(output_dir)

    versioned_dir = output_dir / f"v{version}"
    versioned_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading features from {input_path}...")
    features: list[dict[str, Any]] = load_json(input_path)
    logger.info(f"Loaded {len(features)} records")

    df = pd.DataFrame(features)

    label_columns = settings.stratify_labels
    logger.info("Label distribution in dataset:")
    for col in label_columns:
        if col in df.columns:
            positive_count = df[col].sum()
            positive_percentage = 100 * positive_count / len(df)
            logger.info(
                f"  {col}: {positive_count}/{len(df)} ({positive_percentage:.1f}%)"
            )

    df = df.sort_values("repo_url").reset_index(drop=True)

    output_csv = versioned_dir / "dataset.csv"
    df.to_csv(output_csv, index=False)
    logger.info(f"Saved dataset to {output_csv}")

    checksum = _compute_checksum(output_csv)
    logger.info(f"Dataset checksum: {checksum}")

    pipeline_stats = {}
    logs_dir = settings.logs_dir
    if logs_dir.exists():
        log_files = sorted(logs_dir.glob("extraction_*.log"))
        if log_files:
            latest_log = log_files[-1]
            pipeline_stats["extraction_log"] = str(latest_log.name)

    manifest: dict[str, Any] = {
        "version": version,
        "created_at": datetime.now(UTC).isoformat(),
        "script": "src/data/build_dataset.py",
        "git_commit": _get_git_commit(),
        "input_source": str(input_path),
        "pipeline_stats": pipeline_stats,
        "schema": {
            "total_features": len(df.columns),
            "total_rows": len(df),
            "feature_columns": list(df.columns),
        },
        "checksum": checksum,
    }

    manifest_path = versioned_dir / "manifest.json"
    save_json(manifest, manifest_path)
    logger.info(f"Saved manifest to {manifest_path}")

    logger.info("=" * 60)
    logger.info(f"Dataset build complete: v{version}")
    logger.info(f"Total samples: {len(df)}")
    logger.info(f"Total features: {len(df.columns)}")
    logger.info(f"Output: {output_csv}")
    logger.info("=" * 60)


if __name__ == "__main__":
    build_dataset()
