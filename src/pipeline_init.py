"""Pipeline initialization for the config-recommendation-ml project."""

import json
from datetime import UTC, datetime
from pathlib import Path

from src.config import settings
from src.logger import get_logger
from src.utils import save_config_snapshot

logger = get_logger(__name__)

INIT_SNAPSHOT = Path("logs/pipeline_init.json")


def pipeline_init() -> None:
    """Initialize the pipeline by logging config and saving a snapshot."""
    run_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    logger.info("=" * 80)
    logger.info("Pipeline Initialisation")
    logger.info("=" * 80)
    logger.info(f"Run ID: {run_id}")

    config = settings.to_reproducible_dict()
    config_json = json.dumps(config, indent=2, default=str)
    logger.info(f"Config:\n{config_json}")

    # Timestamped snapshot for audit trail
    snapshot_path = save_config_snapshot(run_id)
    logger.info(f"Config snapshot saved: {snapshot_path}")

    # Fixed-name output tracked by DVC so downstream stages depend on this step
    INIT_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    with open(INIT_SNAPSHOT, "w") as f:
        json.dump({"run_id": run_id, "config": config}, f, indent=2, default=str)


if __name__ == "__main__":
    pipeline_init()
