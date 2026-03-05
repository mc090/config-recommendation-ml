"""Extract file/directory structure facts from raw GitHub repository metadata."""

import re
from pathlib import Path, PurePosixPath
from typing import Any

from src.config import settings
from src.data.utils import load_json, save_json
from src.logger import get_logger

logger = get_logger(__name__)

# Matches Python test files by pytest naming conventions.
_TEST_FILE_RE = re.compile(
    r"(^|/)test_[^/]+\.py$"  # test_*.py at any depth
    r"|[^/]+_test\.py$",  # *_test.py at any depth
    re.IGNORECASE,
)

# Filenames (case-insensitive) that declare Python project dependencies.
_DEPENDENCY_FILENAMES = frozenset(
    {
        "requirements.txt",
        "requirements-dev.txt",
        "requirements_dev.txt",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "pipfile",
    }
)


def _is_test_file(path: str) -> bool:
    """Return True when path matches a recognised test-file pattern."""
    return bool(_TEST_FILE_RE.search(path))


def _is_dependency_file(p: PurePosixPath) -> bool:
    """Return True when the file is a known Python dependency declaration file."""
    if p.name.lower() in _DEPENDENCY_FILENAMES:
        return True

    is_directly_inside_requirements_dir = (
        len(p.parts) == 2 and p.parts[0].lower() == "requirements"
    )
    is_txt_file = p.suffix.lower() == ".txt"

    return is_directly_inside_requirements_dir and is_txt_file


def _extract_one(record: dict[str, Any]) -> dict[str, Any]:
    """Extract structural facts from a single raw record (repo + tree)."""
    repo = record["repo"]
    nodes = record["tree"]["tree"]

    blobs: list[dict[str, Any]] = []
    dir_paths: list[str] = []

    for n in nodes:
        if n.get("type") == "blob":
            blobs.append(n)
        else:
            dir_paths.append(n["path"])

    py_files: list[dict[str, Any]] = []
    js_files: list[dict[str, Any]] = []
    ts_files: list[dict[str, Any]] = []
    html_files: list[dict[str, Any]] = []
    css_files: list[dict[str, Any]] = []
    json_files: list[dict[str, Any]] = []
    sh_files: list[dict[str, Any]] = []
    yaml_files: list[dict[str, Any]] = []
    test_files: list[dict[str, Any]] = []
    docs_files: list[dict[str, Any]] = []
    notebook_files: list[dict[str, Any]] = []
    other_files: list[dict[str, Any]] = []
    dependency_files: list[str] = []
    top_level_dirs_set: set[str] = set()

    has_pyproject_toml = False
    has_dockerfile = False
    has_github_actions = False
    has_requirements_txt = False
    has_conda_env_file = False
    has_docker_compose = False
    has_precommit_config = False
    has_setup_py = False
    has_tox_ini = False
    has_makefile = False
    has_license = False

    for blob in blobs:
        path = blob["path"]
        size = blob.get("size", 0)
        info: dict[str, Any] = {"path": path, "size": size}

        # Parse path once; reuse p, ext, name throughout.
        p = PurePosixPath(path)
        ext = p.suffix.lower()
        name = p.name.lower()
        at_root = len(p.parts) == 1

        if not at_root:
            top_level_dirs_set.add(p.parts[0])

        has_pyproject_toml = has_pyproject_toml or name == "pyproject.toml"
        has_dockerfile = has_dockerfile or name == "dockerfile"
        has_github_actions = has_github_actions or (
            path.startswith(".github/workflows/") and ext in {".yml", ".yaml"}
        )
        has_requirements_txt = (
            has_requirements_txt
            or path == "requirements.txt"
            or (path.startswith("requirements/") and ext == ".txt")
        )
        has_conda_env_file = has_conda_env_file or (
            name.startswith(("environment", "conda")) and ext in {".yml", ".yaml"}
        )
        has_docker_compose = has_docker_compose or name in {
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        }
        has_precommit_config = has_precommit_config or path == ".pre-commit-config.yaml"
        has_setup_py = has_setup_py or path == "setup.py"
        has_tox_ini = has_tox_ini or path == "tox.ini"
        has_makefile = has_makefile or (name == "makefile" and at_root)
        has_license = has_license or (
            name in {"license", "license.md", "license.txt"} and at_root
        )

        if _is_dependency_file(p):
            dependency_files.append(path)
        if _is_test_file(path):
            test_files.append(info)
            continue

        match ext:
            case ".py":
                py_files.append(info)
            case ".js" | ".mjs" | ".cjs":
                js_files.append(info)
            case ".ts" | ".tsx":
                ts_files.append(info)
            case ".html" | ".htm":
                html_files.append(info)
            case ".css":
                css_files.append(info)
            case ".json":
                json_files.append(info)
            case ".sh":
                sh_files.append(info)
            case ".yml" | ".yaml":
                yaml_files.append(info)
            case ".md" | ".rst":
                docs_files.append(info)
            case ".ipynb":
                notebook_files.append(info)
            case _:
                other_files.append(info)

    top_level_dirs_set.update(d for d in dir_paths if "/" not in d)
    top_level_dirs: list[str] = sorted(top_level_dirs_set)
    has_dedicated_test_dir = any(
        d.lower() in {"tests", "test", "__tests__"} for d in top_level_dirs
    )
    has_src_dir = any(d.lower() == "src" for d in top_level_dirs)
    has_docs_dir = any(d.lower() in {"docs", "doc"} for d in top_level_dirs)
    has_scripts_dir = any(d.lower() in {"scripts", "bin"} for d in top_level_dirs)

    return {
        "repo_url": repo["html_url"],
        "stars": repo["stargazers_count"],
        "forks": repo["forks_count"],
        "created_at": repo["created_at"],
        "last_updated": repo["updated_at"],
        "repo_size_kb": repo.get("size", 0),
        "open_issues_count": repo.get("open_issues_count", 0),
        "language": repo.get("language"),
        "tree_truncated": record["tree"].get("truncated", False),
        "py_files": py_files,
        "js_files": js_files,
        "ts_files": ts_files,
        "html_files": html_files,
        "css_files": css_files,
        "json_files": json_files,
        "sh_files": sh_files,
        "yaml_files": yaml_files,
        "test_files": test_files,
        "docs_files": docs_files,
        "notebook_files": notebook_files,
        "other_files": other_files,
        "dirs": dir_paths,
        "has_dedicated_test_dir": has_dedicated_test_dir,
        "has_license": has_license,
        "has_src_dir": has_src_dir,
        "has_docs_dir": has_docs_dir,
        "has_scripts_dir": has_scripts_dir,
        "dependency_files": dependency_files,
        "has_pyproject_toml": has_pyproject_toml,
        "has_dockerfile": has_dockerfile,
        "has_github_actions": has_github_actions,
        "has_requirements_txt": has_requirements_txt,
        "has_conda_env_file": has_conda_env_file,
        "has_docker_compose": has_docker_compose,
        "has_precommit_config": has_precommit_config,
        "has_setup_py": has_setup_py,
        "has_tox_ini": has_tox_ini,
        "has_makefile": has_makefile,
    }


def extract_structure(
    input_path: Path | None = None,
    output_path: Path | None = None,
) -> None:
    """Extract structural facts from raw repo metadata."""
    input_path = input_path or settings.raw_data_path
    output_path = output_path or settings.structure_path

    raw_records: list[dict[str, Any]] = load_json(input_path)
    logger.info(f"Processing {len(raw_records)} raw records...")

    structures: list[dict[str, Any]] = []
    for i, record in enumerate(raw_records, 1):
        repo_name = record["repo"]["full_name"]
        try:
            result = _extract_one(record)
            structures.append(result)
            logger.info(f"[{i}/{len(raw_records)}] {repo_name}: OK")
        except Exception as exc:
            logger.warning(f"[{i}/{len(raw_records)}] {repo_name}: skipped — {exc}")

    save_json(structures, output_path)
    logger.info(f"extract_structure complete: {len(structures)} records written")


if __name__ == "__main__":
    extract_structure()
