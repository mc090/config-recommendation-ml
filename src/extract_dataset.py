import json
from datetime import datetime, timezone

from src.config import settings
from src.logger import get_logger
from src.utils import save_config_snapshot

logger = get_logger(__name__)


def extract_dataset() -> None:
    """Main extraction logic."""
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Log config (without secrets)
    logger.info("=" * 80)
    logger.info("Dataset Extraction Started")
    logger.info("=" * 80)
    logger.info(f"Run ID: {run_id}")

    # Get reproducible config dict
    config_data = settings.to_reproducible_dict()
    config_json = json.dumps(config_data, indent=2, default=str)
    logger.info(f"Config: {config_json}")

    # Save config snapshot
    snapshot_path = save_config_snapshot(run_id)
    logger.info(f"Config snapshot saved: {snapshot_path}")

    # TODO: Actual extraction logic here
    logger.info("Extraction logic not yet implemented")

    logger.info("=" * 80)
    logger.info("Dataset Extraction Completed")
    logger.info("=" * 80)


if __name__ == "__main__":
    extract_dataset()
