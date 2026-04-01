"""Fetch raw repository metadata and git trees from GitHub."""

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
    """Construct a GitHub repository-search query string WITHOUT star filters.

    Star filters are handled separately by the adaptive batching algorithm.
    """
    parts = ["language:Python"]

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
    """Fetch raw repository metadata and git trees from GitHub."""
    cfg = cfg or settings
    rng = random.Random(cfg.random_seed)
    output_path = output_path or cfg.raw_data_path

    base_query = _build_search_query(cfg)
    logger.info(
        f"base_query: {base_query!r}  "
        f"min_stars: {cfg.min_stars}  "
        f"target: {cfg.max_repos}"
    )
    all_repos = github_client.search_repos(
        base_query, min_stars=cfg.min_stars, limit=cfg.max_repos
    )
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

    loss_percent = 100 * (len(all_repos) - len(records)) / len(all_repos)

    logger.info("=" * 60)
    logger.info("Fetch_raw complete")
    logger.info(f"  Input: {len(all_repos)} repos from search")
    logger.info(f"  Output: {len(records)} records with trees")
    logger.info(f"  Loss: {len(all_repos) - len(records)} repos ({loss_percent:.1f}%)")
    logger.info(f"  File: {output_path}")
    logger.info("=" * 60)

    save_json(records, output_path)


if __name__ == "__main__":
    fetch_raw()
