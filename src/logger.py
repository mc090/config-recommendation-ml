"""Logging configuration for the config-recommendation-ml project."""

import logging
from datetime import UTC, datetime


def get_logger(name: str) -> logging.Logger:
    """Configure logging with config snapshot."""
    from src.config import settings

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    log_file = settings.logs_dir / f"extraction_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )

    logger = logging.getLogger(name)
    return logger
