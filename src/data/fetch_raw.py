"""Fetch raw repository metadata and git trees from GitHub.

This module implements the first stage of the data pipeline, which queries the
GitHub API for repositories matching criteria defined in the config, and retrieves their
metadata and git trees. The output is saved as a JSON file for later processing.
"""

import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import requests

from src.config import Settings, settings
from src.data.utils import save_json
from src.github_client import github_client
from src.logger import get_logger

logger = get_logger(__name__)


def _build_search_query(cfg: Settings) -> str:
    """Construct a GitHub repository-search query string."""
    parts = ["language:Python", f"stars:>={cfg.min_stars}"]

    if cfg.min_size_kb > 0 and cfg.max_size_kb is not None:
        parts.append(f"size:{cfg.min_size_kb}..{cfg.max_size_kb}")
    elif cfg.min_size_kb > 0:
        parts.append(f"size:>={cfg.min_size_kb}")

    if cfg.max_time_since_update_days > 0:
        cutoff = datetime.now(UTC) - timedelta(days=cfg.max_time_since_update_days)
        parts.append(f"pushed:>={cutoff.strftime('%Y-%m-%d')}")

    if cfg.exclude_forks:
        parts.append("fork:false")

    if cfg.exclude_archived:
        parts.append("archived:false")

    return " ".join(parts)


def fetch_raw(cfg: Settings | None = None, output_path: Path | None = None) -> None:
    """Fetch raw repository metadata and git trees from GitHub.

    Applies search criteria from config to filter repositories.
    """
    cfg = cfg or settings
    rng = random.Random(cfg.random_seed)
    output_path = output_path or cfg.raw_data_path

    query = _build_search_query(cfg)
    logger.info(f"query: {query!r}  target: {cfg.max_repos}")
    all_repos = github_client.search_repos(query, limit=cfg.max_repos)
    logger.info(f"collected {len(all_repos)} repos")

    rng.shuffle(all_repos)
    logger.info(f"Shuffled {len(all_repos)} repos (seed={cfg.random_seed})")

    records: list[dict[str, Any]] = []
    for i, repo in enumerate(all_repos, 1):
        owner = repo["owner"]["login"]
        name = repo["name"]
        default_branch = repo["default_branch"]
        logger.info(f"[{i}/{len(all_repos)}] {owner}/{name}")

        try:
            tree_sha = github_client.get_default_branch_tree_sha(
                owner, name, default_branch
            )
            tree = github_client.get_tree(owner, name, tree_sha)
        except requests.HTTPError as exc:
            logger.warning(f"Skipping {owner}/{name}: {exc}")
            continue

        records.append({"repo": repo, "tree": tree})

    save_json(records, output_path)
    logger.info(f"fetch_raw complete: {len(records)} records")


if __name__ == "__main__":
    fetch_raw()
