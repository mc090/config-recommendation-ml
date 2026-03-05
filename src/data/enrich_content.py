"""Enrich structural metadata with file-content metrics via the GitHub API."""

import configparser
import json
import tomllib
from pathlib import Path, PurePosixPath
from typing import Any

from src.config import settings
from src.data.utils import load_json, save_json
from src.github_client import github_client
from src.logger import get_logger

logger = get_logger(__name__)


def _owner_repo(repo_url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub HTML URL."""
    parts = repo_url.rstrip("/").split("/")
    return parts[-2], parts[-1]


def _nb_cell_count(text: str) -> int | None:
    """Return total cell count from a .ipynb JSON string, or None if unparseable."""
    try:
        nb = json.loads(text)
        return len(nb.get("cells", []))
    except json.JSONDecodeError:
        return None


def _count_requirements_deps(text: str) -> int:
    """Count non-empty, non-comment, non-option lines in a requirements*.txt file."""
    return sum(
        1
        for line in text.splitlines()
        if (stripped := line.strip()) and not stripped.startswith(("#", "-"))
    )


def _count_pyproject_deps(text: str) -> int:
    """Count declared dependencies in a pyproject.toml (PEP 621 and Poetry)."""
    try:
        data = tomllib.loads(text)
    except Exception:
        return 0

    deps: list[str] = []
    deps.extend(data.get("project", {}).get("dependencies", []))

    poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    deps.extend(k for k in poetry_deps if k.lower() != "python")

    return len(deps)


def _count_setup_cfg_deps(text: str) -> int:
    """Count install_requires entries in a setup.cfg file."""
    parser = configparser.ConfigParser()
    try:
        parser.read_string(text)
        raw = parser.get("options", "install_requires", fallback="")
        return sum(1 for line in raw.splitlines() if line.strip())
    except Exception:
        return 0


def _count_pipfile_deps(text: str) -> int:
    """Count package entries in the [packages] section of a Pipfile."""
    in_packages = False
    count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_packages = stripped.lower() == "[packages]"
            continue
        if in_packages and stripped and not stripped.startswith("#"):
            count += 1
    return count


def _only_setup_py_deps(dependency_files: list[str]) -> bool:
    """Return True if setup.py is the only dependency file present (unparseable)."""
    if not dependency_files:
        return False
    return all(PurePosixPath(p).name.lower() == "setup.py" for p in dependency_files)


def _count_file_deps(path: str, text: str) -> int:
    """Dispatch to the correct dependency counter based on file name."""
    name = PurePosixPath(path).name.lower()
    match name:
        case "pyproject.toml":
            return _count_pyproject_deps(text)
        case "setup.cfg":
            return _count_setup_cfg_deps(text)
        case "pipfile":
            return _count_pipfile_deps(text)
        case "setup.py":
            logger.debug(f"Skipping dependency count for {path} (can't parse reliably)")
            return 0
        case _:
            return _count_requirements_deps(text)


def _read_local(repo_root: Path, rel_path: str) -> str | None:
    """Read a file from the extracted tarball root, or return None if missing."""
    file_path = repo_root / rel_path
    if not file_path.is_file():
        return None
    try:
        return file_path.read_text(errors="replace")
    except OSError:
        return None


def _enrich_one(record: dict[str, Any]) -> dict[str, Any]:
    """Add avg_py_file_len, avg_docs_file_len, avg_nb_cell_count, num_dependencies."""
    owner, repo = _owner_repo(record["repo_url"])

    with github_client.repo_tarball(owner, repo) as repo_root:
        # avg_py_file_len
        py_lens: list[int] = []
        for f in record.get("py_files", []):
            text = _read_local(repo_root, f["path"])
            if text is not None:
                py_lens.append(len(text.splitlines()))
        record["avg_py_file_len"] = sum(py_lens) / len(py_lens) if py_lens else 0

        # avg_test_file_len
        test_lens: list[int] = []
        for f in record.get("test_files", []):
            text = _read_local(repo_root, f["path"])
            if text is not None:
                test_lens.append(len(text.splitlines()))
        record["avg_test_file_len"] = (
            sum(test_lens) / len(test_lens) if test_lens else 0
        )

        # avg_docs_file_len
        docs_lens: list[int] = []
        for f in record.get("docs_files", []):
            text = _read_local(repo_root, f["path"])
            if text is not None:
                docs_lens.append(len(text.splitlines()))
        record["avg_docs_file_len"] = (
            sum(docs_lens) / len(docs_lens) if docs_lens else 0
        )

        # avg_nb_cell_count
        nb_counts: list[int] = []
        for f in record.get("notebook_files", []):
            text = _read_local(repo_root, f["path"])
            if text is not None:
                count = _nb_cell_count(text)
                if count is not None:
                    nb_counts.append(count)
        record["avg_nb_cell_count"] = (
            sum(nb_counts) / len(nb_counts) if nb_counts else 0
        )

        # num_dependencies
        total_deps = 0
        for path in record.get("dependency_files", []):
            text = _read_local(repo_root, path)
            if text is not None:
                total_deps += _count_file_deps(path, text)
        record["num_dependencies"] = total_deps

    return record


def enrich_content(
    input_path: Path | None = None,
    output_path: Path | None = None,
) -> None:
    """Enrich structural records with file-content metrics from GitHub API."""
    input_path = input_path or settings.structure_path
    output_path = output_path or settings.structure_enriched_path

    records: list[dict[str, Any]] = load_json(input_path)
    logger.info(f"Enriching {len(records)} records...")

    enriched: list[dict[str, Any]] = []

    skipped = 0
    for i, record in enumerate(records, 1):
        repo_url = record["repo_url"]
        if _only_setup_py_deps(record.get("dependency_files", [])):
            logger.info(
                f"[{i}/{len(records)}] {repo_url}: excluded — "
                "setup.py is the only dependency file"
            )
            skipped += 1
            continue
        try:
            result = _enrich_one(record)
            enriched.append(result)
            logger.info(f"[{i}/{len(records)}] {repo_url}: OK")
        except Exception as exc:
            logger.warning(f"[{i}/{len(records)}] {repo_url}: skipped — {exc}")

    if skipped:
        logger.info(
            f"Excluded {skipped} record(s) with setup.py as the only dependency file"
        )

    save_json(enriched, output_path)
    logger.info(f"enrich_content complete: {len(enriched)} records written")


if __name__ == "__main__":
    enrich_content()
