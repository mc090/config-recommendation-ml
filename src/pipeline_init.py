"""Pipeline initialization for the config-recommendation-ml project."""

import json
from datetime import UTC, datetime

from src.config import settings
from src.logger import get_logger
from src.utils import save_config_snapshot

logger = get_logger(__name__)


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

    snapshot_path = save_config_snapshot(run_id)
    logger.info(f"Config snapshot saved: {snapshot_path}")

    with open(settings.pipeline_init_snapshot, "w") as f:
        json.dump({"run_id": run_id, "config": config}, f, indent=2, default=str)


if __name__ == "__main__":
    pipeline_init()
