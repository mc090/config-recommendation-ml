"""Fetch raw repository metadata and git trees from GitHub.

This module implements the first stage of the data pipeline, which queries the
GitHub API for repositories matching criteria defined in the config, and retrieves their
metadata and git trees. The output is saved as a JSON file for later processing.
"""

import json
import random
import time
from datetime import UTC, datetime, timedelta
from math import ceil
from pathlib import Path
from typing import Any

import requests

from src.config import Settings, settings
from src.logger import get_logger

logger = get_logger(__name__)


def _build_search_query(language: str, cfg: Settings) -> str:
    """Construct a GitHub repository-search query string for one language."""
    parts = [f"language:{language}", f"stars:>={cfg.min_stars}"]

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


class GitHubClient:
    """Thin wrapper around the GitHub REST API with sliding-window throttling."""

    def __init__(self, cfg: Settings) -> None:
        """Initialize GitHub API client with authentication and throttling."""
        self._cfg = cfg
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {cfg.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )
        self._request_times: list[float] = []

    def _throttle(self) -> None:
        """Block until sending another request is within the configured rate."""
        now = time.monotonic()
        self._request_times = [t for t in self._request_times if now - t < 60.0]

        if len(self._request_times) >= self._cfg.requests_per_minute:
            wait = 60.0 - (now - self._request_times[0]) + 0.1
            logger.debug(f"Rate limit reached — sleeping {wait:.1f}s")
            time.sleep(wait)

        self._request_times.append(time.monotonic())

    def get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a GET request to the GitHub API with throttling."""
        self._throttle()
        response = self._session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def search_repos(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search repositories with pagination, respecting the GitHub Search API limits.

        Uses pagination to handle the GitHub Search API's 1000-result cap.
        """
        repos: list[dict[str, Any]] = []
        page = 1
        per_page = min(100, limit)

        while len(repos) < limit:
            data = self.get(
                "https://api.github.com/search/repositories",
                params={
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": per_page,
                    "page": page,
                },
            )
            items = data.get("items", [])
            repos.extend(items)
            logger.debug(f"page {page}: {len(items)} results (total: {len(repos)})")

            if len(items) < per_page:
                break
            if page >= 10:
                logger.warning("GitHub Search API 1000-result cap reached.")
                break
            page += 1

        return repos[:limit]

    def get_tree(self, owner: str, repo: str, tree_sha: str) -> dict[str, Any]:
        """Fetch the full recursive git tree for a repository."""
        tree = self.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/trees/{tree_sha}",
            params={"recursive": "1"},
        )
        if tree.get("truncated"):
            logger.warning(f"{owner}/{repo}: git tree truncated (repo too large)")
        return tree

    def get_default_branch_tree_sha(self, owner: str, repo: str, branch: str) -> str:
        """Resolve the root tree SHA for the HEAD commit of *branch*."""
        url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}"
        info = self.get(url)
        return info["commit"]["commit"]["tree"]["sha"]


# ---------------------------------------------------------------------------
# Stage entrypoint
# ---------------------------------------------------------------------------


def fetch_raw(
    cfg: Settings | None = None, output_path: Path | str | None = None
) -> None:
    """Fetch raw repository metadata and git trees from GitHub.

    Applies search criteria from config to filter repositories.
    """
    cfg = cfg or settings
    client = GitHubClient(cfg)
    rng = random.Random(cfg.random_seed)
    raw_data_path = Path(output_path) if output_path is not None else cfg.raw_data_path

    n_languages = len(cfg.languages)
    per_language = ceil(cfg.max_repos / n_languages)

    all_repos: list[dict[str, Any]] = []
    for language in cfg.languages:
        query = _build_search_query(language, cfg)
        logger.info(f"[{language}] query: {query!r}  target: {per_language}")
        repos = client.search_repos(query, limit=per_language)
        logger.info(f"[{language}] collected {len(repos)} repos")
        all_repos.extend(repos)

    rng.shuffle(all_repos)
    all_repos = all_repos[: cfg.max_repos]
    logger.info(f"Sampled {len(all_repos)} repos total (seed={cfg.random_seed})")

    records: list[dict[str, Any]] = []
    for i, repo in enumerate(all_repos, 1):
        owner = repo["owner"]["login"]
        name = repo["name"]
        default_branch = repo.get("default_branch", "main")
        logger.info(f"[{i}/{len(all_repos)}] {owner}/{name}")

        try:
            tree_sha = client.get_default_branch_tree_sha(owner, name, default_branch)
            tree = client.get_tree(owner, name, tree_sha)
        except requests.HTTPError as exc:
            logger.warning(f"Skipping {owner}/{name}: {exc}")
            continue

        records.append({"repo": repo, "tree": tree})

    raw_data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(raw_data_path, "w") as f:
        json.dump(records, f)

    logger.info(f"Saved {len(records)} records → {raw_data_path}")


if __name__ == "__main__":
    fetch_raw()
