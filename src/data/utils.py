"""Shared I/O utilities for data pipeline stages."""

import json
from pathlib import Path
from typing import Any

from src.logger import get_logger

logger = get_logger(__name__)


def load_json(path: Path | str) -> Any:
    """Load JSON from *path*, logging record count when the root value is a list."""
    path = Path(path)
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, list):
        logger.debug(f"Loaded {len(data)} records from {path}")
    return data


def save_json(data: Any, path: Path | str, *, indent: int = 2) -> None:
    """Serialise *data* to JSON at *path*, creating parent directories as needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=indent, default=str)
    n = len(data) if isinstance(data, list) else 1
    logger.info(f"Saved {n} records -> {path}")
