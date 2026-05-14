"""Reproducibility-focused utility helpers."""

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from src.logger import get_logger

logger = get_logger(__name__)


def save_config_snapshot(run_id: str) -> Path:
    """Save reproducible config snapshot in logs directory."""
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


def get_git_commit() -> str:
    """Return current git commit hash."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()
