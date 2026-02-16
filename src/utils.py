import json
from datetime import datetime, timezone
from pathlib import Path


def save_config_snapshot(run_id: str) -> Path:
    """
    Save reproducible config snapshot alongside dataset.

    This allows future you (or reviewers) to know EXACTLY how the dataset was created.
    """
    from src.config import settings

    snapshot_path = settings.output_dir / f"config_{run_id}.json"

    with open(snapshot_path, "w") as f:
        json.dump(
            {
                "run_id": run_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "config": settings.to_reproducible_dict(),
            },
            f,
            indent=2,
        )

    return snapshot_path
