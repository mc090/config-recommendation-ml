"""GitHub API client with sliding-window throttling."""

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


class GitHubClient:
    """Thin wrapper around the GitHub REST API with sliding-window throttling."""

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

    def _throttle(self) -> None:
        """Block until sending another request is within the configured rate."""
        now = time.monotonic()
        self._request_times = [t for t in self._request_times if now - t < 60.0]

        if len(self._request_times) >= settings.requests_per_minute:
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
