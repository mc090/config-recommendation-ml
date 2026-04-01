"""GitHub API client with sliding-window throttling and greedy batching.

This module provides a GitHubClient wrapper for the GitHub REST API with:
- Rate limiting (30 req/min for Search API, configurable for REST API)
- Secondary rate limit protection (minimum delay between requests)
- Automatic retry with exponential backoff for rate limit errors
- Greedy star-based batching to bypass the 1000-result Search API limit
- Quality-prioritized repository collection (descending by stars)
"""

import tarfile
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import requests

from src.config import settings
from src.logger import get_logger

logger = get_logger(__name__)

# Maximum number of retries for rate limit errors
MAX_RETRIES = 5


def _calculate_retry_wait(response: requests.Response, attempt: int) -> int:
    """Calculate wait time for retry based on headers or exponential backoff."""
    retry_after = response.headers.get("Retry-After")
    x_ratelimit_remaining = response.headers.get("X-RateLimit-Remaining")
    x_ratelimit_reset = response.headers.get("X-RateLimit-Reset")

    if retry_after:
        return int(retry_after)
    elif x_ratelimit_remaining == "0" and x_ratelimit_reset:
        return max(int(x_ratelimit_reset) - int(time.time()), 0) + 1
    else:
        # Exponential backoff: 2s, 4s, 8s, 16s, 32s
        return (2**attempt) * 2


class GitHubClient:
    """GitHub REST API client with rate limiting and greedy batching."""

    def __init__(self) -> None:
        """Initialize GitHub API client with authentication and throttling."""
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {settings.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )
        self._request_times: list[float] = []
        self._last_request_time: float = 0.0

    def _throttle(self, is_search_api: bool = False) -> None:
        """Block until sending another request is within the configured rate.

        Args:
            is_search_api:
                If True, use GitHub's hard limit of 30 req/min for Search API
                If False, use configured requests_per_minute for REST API.
        """
        rate_limit = (
            settings.GITHUB_SEARCH_API_LIMIT
            if is_search_api
            else settings.requests_per_minute
        )

        now = time.monotonic()
        self._request_times = [t for t in self._request_times if now - t < 60.0]

        if len(self._request_times) >= rate_limit:
            wait = 60.0 - (now - self._request_times[0]) + 0.1
            api_type = "Search API" if is_search_api else "REST API"
            logger.debug(
                f"{api_type} rate limit ({rate_limit} req/min) reached — "
                f"sleeping {wait:.1f}s"
            )
            time.sleep(wait)
            now = time.monotonic()

        time_since_last = now - self._last_request_time
        if time_since_last < settings.min_request_delay:
            delay = settings.min_request_delay - time_since_last
            logger.debug(f"Secondary rate limit protection: sleeping {delay:.2f}s")
            time.sleep(delay)
            now = time.monotonic()

        self._request_times.append(now)
        self._last_request_time = now

    def _handle_rate_limit_response(
        self, response: requests.Response, attempt: int
    ) -> bool:
        """Handle rate limit response. Returns True if should retry, False otherwise."""
        if response.status_code not in (403, 429):
            return False

        if attempt >= MAX_RETRIES - 1:
            logger.error(
                f"Rate limit exceeded after {MAX_RETRIES} attempts. "
                f"Response: {response.text[:200]}"
            )
            return False

        wait_time = _calculate_retry_wait(response, attempt)
        logger.warning(
            f"Rate limit hit (HTTP {response.status_code}, "
            f"attempt {attempt + 1}/{MAX_RETRIES}). "
            f"Waiting {wait_time}s before retry..."
        )
        time.sleep(wait_time)
        return True

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        is_search_api: bool = False,
    ) -> dict[str, Any]:
        """Make a GET request to the GitHub API with throttling and retry logic."""
        for attempt in range(MAX_RETRIES):
            try:
                self._throttle(is_search_api=is_search_api)
                response = self._session.get(url, params=params, timeout=30)

                if self._handle_rate_limit_response(response, attempt):
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                if e.response.status_code in (403, 429) and attempt < MAX_RETRIES - 1:
                    wait_time = _calculate_retry_wait(e.response, attempt)
                    logger.warning(
                        f"HTTP {e.response.status_code} error "
                        f"(attempt {attempt + 1}/{MAX_RETRIES}). "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue
                raise
        raise RuntimeError(f"Failed to fetch {url} after {MAX_RETRIES} attempts")

    def search_repos(
        self, base_query: str, min_stars: int, limit: int
    ) -> list[dict[str, Any]]:
        """Search repositories with greedy batching to bypass API's result limit."""
        all_repos: list[dict[str, Any]] = []
        current_max_threshold = None
        batch_num = 1

        logger.info(
            f"Starting greedy batching to collect {limit} repos (min_stars={min_stars})"
        )

        while len(all_repos) < limit:
            remaining = limit - len(all_repos)

            if current_max_threshold is None:
                star_constraint = f"stars:>={min_stars}"
            else:
                star_constraint = f"stars:{min_stars}..{current_max_threshold - 1}"

            batch_query = f"{base_query} {star_constraint}"

            logger.info(
                f"Batch {batch_num}: Fetching repos with {star_constraint} "
                f"(remaining: {remaining})"
            )

            batch_repos, hit_limit = self._fetch_batch_greedy(batch_query, remaining)

            if not batch_repos:
                logger.warning(f"Batch {batch_num} returned no results. Stopping.")
                break

            all_repos.extend(batch_repos)
            logger.info(
                f"Batch {batch_num} complete: +{len(batch_repos)} repos "
                f"(total: {len(all_repos)}/{limit})"
            )

            if not hit_limit and len(batch_repos) < remaining:
                logger.info(f"No more repositories available with stars >= {min_stars}")
                break

            lowest_stars_in_batch = min(
                repo["stargazers_count"] for repo in batch_repos
            )

            if lowest_stars_in_batch == min_stars:
                logger.warning(
                    f"Batch {batch_num} contains >=1000 repos with exactly "
                    f"{min_stars} stars. Cannot collect more without "
                    f"duplicates. Collected {len(all_repos)} total."
                )
                break

            current_max_threshold = lowest_stars_in_batch
            batch_num += 1

        logger.info(
            f"Greedy batching complete: {len(all_repos)} repos "
            f"collected in {batch_num} batch(es)"
        )

        self._check_for_duplicates(all_repos)

        return all_repos[:limit]

    def _check_for_duplicates(self, repos: list[dict[str, Any]]) -> None:
        """Check for duplicate repositories based on full_name."""
        seen = set()
        duplicates = set()
        for repo in repos:
            full_name = repo.get("full_name")
            if full_name in seen:
                duplicates.add(full_name)
            else:
                seen.add(full_name)

        if duplicates:
            raise RuntimeError(
                f"Duplicate repositories found in search results: {duplicates}."
            )

    def _fetch_batch_greedy(
        self, query: str, limit: int
    ) -> tuple[list[dict[str, Any]], bool]:
        """Fetch repositories using pagination until hitting limit or page cap."""
        repos: list[dict[str, Any]] = []
        page = 1
        per_page = 100
        hit_limit = False

        while len(repos) < limit and page <= 10:
            data = self.get(
                "https://api.github.com/search/repositories",
                params={
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": per_page,
                    "page": page,
                },
                is_search_api=True,
            )
            items = data.get("items", [])
            repos.extend(items)
            logger.debug(
                f"  page {page}: {len(items)} results (batch total: {len(repos)})"
            )

            if len(items) < per_page:
                break

            if page == 10:
                hit_limit = True
                logger.debug("  Hit page 10 limit (1000 results)")
                break

            page += 1

        return repos[:limit], hit_limit

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

    @contextmanager
    def repo_tarball(self, owner: str, repo: str) -> Iterator[Path]:
        """Download HEAD tarball, extract to a temp dir, yield the repo root path.

        Counts as a single throttled API call; the actual file transfer is served
        from GitHub's CDN and does not consume additional API rate-limit quota.
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/tarball/HEAD"
        self._throttle()
        response = self._session.get(url, stream=True, timeout=120)
        response.raise_for_status()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            tar_path = tmppath / "repo.tar.gz"
            with open(tar_path, "wb") as fh:
                for chunk in response.iter_content(chunk_size=65_536):
                    fh.write(chunk)
            with tarfile.open(tar_path, "r:gz") as tf:
                tf.extractall(tmppath)
            tar_path.unlink()  # free the compressed archive; only extracted tree needed
            subdirs = [d for d in tmppath.iterdir() if d.is_dir()]
            if not subdirs:
                raise RuntimeError(f"Tarball for {owner}/{repo} is empty")
            yield subdirs[0]


github_client = GitHubClient()
