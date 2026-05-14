"""Logging configuration for the config-recommendation-ml project."""

import logging
from datetime import UTC, datetime
from functools import lru_cache

from src.config import settings


@lru_cache(maxsize=1)
def _setup_logging() -> None:
    """Configure root, project, and third-party logging once per process."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    log_file = settings.logs_dir / f"extraction_{timestamp}.log"

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(levelname)-7s | %(message)s")
        if settings.log_terse_console
        else logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(message)s",
            datefmt="%H:%M:%S",
        )
    )

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.getLogger("src").setLevel(getattr(logging, settings.log_level))
    third_party_level = getattr(logging, settings.third_party_log_level)

    for logger_name in (
        "mlflow",
        "urllib3",
        "git",
        "git.cmd",
        "matplotlib",
        "matplotlib.font_manager",
    ):
        logging.getLogger(logger_name).setLevel(third_party_level)


def get_logger(name: str) -> logging.Logger:
    """Return logger after one-time project logging setup."""
    _setup_logging()
    return logging.getLogger(name)
