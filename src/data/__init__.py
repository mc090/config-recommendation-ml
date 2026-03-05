"""Package-level initialization for the data processing module.

This module handles data fetching, extraction, and feature engineering for
the config-recommendation-ml project.
"""

from .enrich_content import enrich_content
from .extract_structure import extract_structure
from .fetch_raw import fetch_raw

__all__ = [
    "enrich_content",
    "extract_structure",
    "fetch_raw",
]
