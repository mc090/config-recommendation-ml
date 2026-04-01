"""Compute derived features from enriched structure data.

This computes final derived features such as file count ratios, repository age metrics,
and other computed attributes needed for the ML dataset.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.config import settings
from src.data.utils import load_json, save_json
from src.logger import get_logger

logger = get_logger(__name__)


def _compute_test_file_ratio(num_test_files: int, num_py_files: int) -> float:
    """Compute ratio of test files to all Python files."""
    total_py = num_py_files + num_test_files
    if total_py == 0:
        return 0.0
    return round(num_test_files / total_py, 3)


def _compute_avg_files_per_dir(num_files: int, num_dirs: int) -> float:
    """Compute average files per directory.

    The +1 accounts for the repository root directory.
    """
    return round(num_files / (num_dirs + 1), 2)


def _compute_repo_age_days(created_at: str) -> int:
    """Calculate days since repository creation."""
    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    now = datetime.now(UTC)
    return (now - created).days


def _compute_recent_activity_days(updated_at: str) -> int:
    """Calculate days since last repository update."""
    updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    now = datetime.now(UTC)
    return (now - updated).days


def _compute_features_for_record(record: dict[str, Any]) -> dict[str, Any]:
    """Transform enriched record into final feature representation."""
    num_py_files = len(record.get("py_files", []))
    num_js_files = len(record.get("js_files", []))
    num_ts_files = len(record.get("ts_files", []))
    num_html_files = len(record.get("html_files", []))
    num_css_files = len(record.get("css_files", []))
    num_json_files = len(record.get("json_files", []))
    num_sh_files = len(record.get("sh_files", []))
    num_yaml_files = len(record.get("yaml_files", []))
    num_test_files = len(record.get("test_files", []))
    num_docs_files = len(record.get("docs_files", []))
    num_notebooks = len(record.get("notebook_files", []))
    other_extensions_count = len(record.get("other_files", []))
    num_dirs = len(record.get("dirs", []))

    num_files = (
        num_py_files
        + num_js_files
        + num_ts_files
        + num_html_files
        + num_css_files
        + num_json_files
        + num_sh_files
        + num_yaml_files
        + num_test_files
        + num_docs_files
        + num_notebooks
        + other_extensions_count
    )

    test_file_ratio = _compute_test_file_ratio(num_test_files, num_py_files)
    avg_files_per_dir = _compute_avg_files_per_dir(num_files, num_dirs)
    repo_age_days = _compute_repo_age_days(record["created_at"])
    recent_activity_days = _compute_recent_activity_days(record["last_updated"])

    features: dict[str, int | float] = {
        # Identifier
        "repo_url": record["repo_url"],
        # Repository metadata from GitHub API
        "stars": record["stars"],
        "forks": record["forks"],
        "repo_size_kb": record["repo_size_kb"],
        "open_issues_count": record["open_issues_count"],
        # File type counts
        "num_files": num_files,
        "num_py_files": num_py_files,
        "num_js_files": num_js_files,
        "num_ts_files": num_ts_files,
        "num_html_files": num_html_files,
        "num_css_files": num_css_files,
        "num_json_files": num_json_files,
        "num_sh_files": num_sh_files,
        "num_yaml_files": num_yaml_files,
        "num_test_files": num_test_files,
        "test_file_ratio": test_file_ratio,
        "num_docs_files": num_docs_files,
        "num_notebooks": num_notebooks,
        "other_extensions_count": other_extensions_count,
        # Directory features
        "has_dedicated_test_dir": record["has_dedicated_test_dir"],
        "has_license": record["has_license"],
        "has_src_dir": record["has_src_dir"],
        "has_docs_dir": record["has_docs_dir"],
        "has_scripts_dir": record["has_scripts_dir"],
        "num_dirs": num_dirs,
        "avg_files_per_dir": avg_files_per_dir,
        # File content metrics (computed in enrich_content step)
        "avg_py_file_len": round(record.get("avg_py_file_len", 0.0), 1),
        "avg_test_file_len": round(record.get("avg_test_file_len", 0.0), 1),
        "avg_nb_cell_count": round(record.get("avg_nb_cell_count", 0.0), 1),
        "avg_docs_file_len": round(record.get("avg_docs_file_len", 0.0), 1),
        "num_dependencies": record.get("num_dependencies", 0),
        # Date features
        "repo_age_days": repo_age_days,
        "recent_activity_days": recent_activity_days,
        # Labels
        "has_pyproject_toml": record["has_pyproject_toml"],
        "has_dockerfile": record["has_dockerfile"],
        "has_github_actions": record["has_github_actions"],
        "has_requirements_txt": record["has_requirements_txt"],
        "has_conda_env_file": record["has_conda_env_file"],
        "has_docker_compose": record["has_docker_compose"],
        "has_precommit_config": record["has_precommit_config"],
        "has_setup_py": record["has_setup_py"],
        "has_tox_ini": record["has_tox_ini"],
        "has_makefile": record["has_makefile"],
    }

    return features


def compute_features(
    input_path: Path | None = None,
    output_path: Path | None = None,
) -> None:
    """Compute final features from content-enriched structure data."""
    input_path = input_path or settings.structure_enriched_path
    output_path = output_path or settings.computed_features_path

    records: list[dict[str, Any]] = load_json(input_path)
    logger.info(f"Computing features for {len(records)} records...")

    features: list[dict[str, Any]] = []
    for i, record in enumerate(records, 1):
        repo_url = record["repo_url"]
        try:
            feature_record = _compute_features_for_record(record)
            features.append(feature_record)
            logger.info(f"[{i}/{len(records)}] {repo_url}: OK")
        except Exception as exc:
            logger.warning(
                f"[{i}/{len(records)}] {repo_url}: failed — {exc}", exc_info=True
            )

    loss_percent = 100 * (len(records) - len(features)) / len(records)

    logger.info("=" * 60)
    logger.info("Compute_features complete")
    logger.info(f"  Input: {len(records)} enriched records")
    logger.info(f"  Output: {len(features)} feature records")
    logger.info(f"  Loss: {len(records) - len(features)} repos ({loss_percent:.1f}%)")
    logger.info(f"  File: {output_path}")
    logger.info("=" * 60)

    save_json(features, output_path)


if __name__ == "__main__":
    compute_features()
