# Dataset Card

## Name and Version
- **Name**: Public GitHub Repositories Structure Metadata
- **Version**: 1.0.0

## Motivation
My motivation for creating this dataset is to explore the process of building a custom dataset and to have a dedicated resource for further processing in machine learning models. This work forms the foundation of my thesis. The dataset focuses exclusively on Python repositories, as the primary label of interest (`has_pyproject_toml`) is Python-specific, and restricting to a single language ecosystem ensures feature coherence and avoids language as a trivial confound.

## Intended Use
The primary intended use is to train machine learning models for configuration recommendation systems. The dataset is also suitable for research in software analytics and automated tooling.

## Data Sources and Selection Criteria
- **Sources**: GitHub repositories collected via the GitHub API.
- **Selection Criteria**: Only repositories whose **primary language is Python** (as reported by the GitHub API `language` field) are included. This decision ensures label coherence (particularly for `has_pyproject_toml`), feature relevance, and a well-defined problem scope. Additional filters (stars, size, activity, forks/archived exclusion) are configured via pipeline settings.

## Label Collection vs. Modelling Scope
All configuration file presence labels listed below are collected and stored in the dataset during extraction. However, not all labels are used as targets in ML experiments — the current modelling scope is limited to the three labels marked as primary. Additional collected labels are retained in the dataset as metadata to support future experiments without requiring data re-collection. The subset used for ML training is documented in the [Model Card](./model_card.md).

## Schema
TBA

### Attributes

> `repo_url` is an identifier/metadata field included for traceability and potential dataset reuse. It must not be used as a model feature.

| Name | Type | Description | Example |
|---|---|---|---|
| `repo_url` | string | Link to the GitHub repository (identifier) | `https://github.com/user/repo` |
| `stars` | int | Number of stars in GitHub repository | `1234` |
| `forks` | int | Number of forks in GitHub repository | `56` |
| `repo_size_kb` | int | Total repository size in kilobytes as reported by the GitHub API | `2048` |
| `open_issues_count` | int | Number of currently open issues | `12` |
| `num_files` | int | Total number of files | `42` |
| `num_py_files` | int | Number of Python (`.py`) files | `12` |
| `num_js_files` | int | Number of JavaScript (`.js`) files | `2` |
| `num_ts_files` | int | Number of TypeScript (`.ts`) files | `0` |
| `num_html_files` | int | Number of HTML (`.html`) files | `1` |
| `num_css_files` | int | Number of CSS (`.css`) files | `0` |
| `num_json_files` | int | Number of JSON (`.json`) files | `3` |
| `num_sh_files` | int | Number of Shell (`.sh`) files | `1` |
| `num_test_files` | int | Number of Python test files matching `test_*.py` or `*_test.py` patterns anywhere in the repository tree | `5` |
| `num_docs_files` | int | Number of documentation files (`.md` or `.rst`) | `2` |
| `num_notebooks` | int | Number of Jupyter Notebook (`.ipynb`) files | `0` |
| `other_extensions_count` | int | Number of files whose extension is not one of: `.py`, `.js`, `.ts`, `.html`, `.css`, `.json`, `.sh`, `.md`, `.rst`, `.ipynb` | `4` |
| `has_dedicated_test_dir` | bool | True if any top-level directory is named `tests`, `test`, or `__tests__` | `true` |
| `has_license` | bool | True if a `LICENSE`, `LICENSE.md`, or `LICENSE.txt` file is present at the repository root | `true` |
| `has_src_dir` | bool | True if a top-level directory named `src/` is present. Specifically identifies the src-layout packaging convention; projects using a named package directory are `false` | `true` |
| `has_docs_dir` | bool | True if a top-level directory named `docs/` or `doc/` is present | `false` |
| `has_scripts_dir` | bool | True if a top-level directory named `scripts/` or `bin/` is present | `false` |
| `num_dirs` | int | Total number of directories | `8` |
| `avg_files_per_dir` | float | Average number of files per directory | `5.25` |
| `avg_py_file_len` | int | Average length of Python files in lines of code | `200` |
| `avg_nb_cell_count` | int | Average number of cells (code + markdown) per Jupyter Notebook file | `24` |
| `avg_docs_file_len` | int | Average length of documentation files in lines | `120` |
| `num_dependencies` | int | Number of unique declared dependencies parsed from `requirements.txt`, `requirements/*.txt`, `Pipfile`, `pyproject.toml` (dependencies table), and `setup.py` (`install_requires`) | `10` |
| `repo_age_days` | int | Days since repository creation (derived from GitHub API `created_at`) | `1500` |
| `recent_activity_days` | int | Days since last repository update (derived from GitHub API `updated_at`) | `20` |

### Labels

> Labels marked **[PRIMARY]** are used as ML targets in current experiments. All other collected labels are stored in the dataset for potential future use. See the [Model Card](./model_card.md) for the active modelling scope.

| Name | Type | Description | Example |
|---|---|---|---|
| `has_pyproject_toml` | bool | **[PRIMARY]** Presence of `pyproject.toml` anywhere in the repository tree | `false` |
| `has_dockerfile` | bool | **[PRIMARY]** Presence of a file named `Dockerfile` anywhere in the repository tree | `false` |
| `has_github_actions` | bool | **[PRIMARY]** Presence of at least one `.yml` or `.yaml` file inside `.github/workflows/` | `true` |
| `has_requirements_txt` | bool | Presence of `requirements.txt` at the repository root or any `.txt` file inside a `requirements/` directory | `true` |
| `has_conda_env_file` | bool | Presence of any `.yml` or `.yaml` file whose name starts with `environment` or `conda` anywhere in the repository tree (e.g. `environment.yml`, `environment-base.yaml`, `conda.yaml`) | `false` |
| `has_docker_compose` | bool | Presence of `docker-compose.yml`, `docker-compose.yaml`, `compose.yml`, or `compose.yaml` anywhere in the repository tree | `false` |
| `has_precommit_config` | bool | Presence of `.pre-commit-config.yaml` anywhere in the repository tree | `false` |
| `has_setup_py` | bool | Presence of `setup.py` at the repository root | `true` |
| `has_tox_ini` | bool | Presence of `tox.ini` at the repository root | `false` |
| `has_makefile` | bool | Presence of `Makefile` at the repository root | `false` |

## Collection and Preprocessing Steps
- **Collection**: TBA
- **Preprocessing**: TBA

## Limitations
- **Limitations**: The dataset may not represent all types of software projects, as it focuses on repositories with specific characteristics that meets intended selection 

## Recommended Splits and Versioning Policy
- **Splits**: Train (70%), Validation (15%), Test (15%).
- **Versioning**: Follow semantic versioning (e.g., 1.0.0). Each processed snapshot includes a manifest file for reproducibility.

## Manifest Template
A manifest file should accompany each processed dataset snapshot. It records provenance and reproducibility information. Example template:

```json
{
  "version": "0.1.0",
  "created_at": "2025-11-14T12:00:00Z",
  "script": "src/data/build_dataset.py",
  "git_commit": "abc123def",
  "preprocessing": {
    "remove_empty_repos": true,
    "min_files": 5
  },
  "rows": 12345,
  "checksum": "sha256:...",
  "notes": "Edit fields to match the produced snapshot. Save alongside the processed dataset."
}
```

- `version`: Semantic version of the snapshot
- `created_at`: ISO8601 timestamp
- `script`: Path to the script used for processing
- `git_commit`: Commit hash of the code used
- `preprocessing`: Dictionary of parameters and steps
- `rows`: Number of rows in the processed dataset
- `checksum`: SHA256 checksum of the main artifact
- `notes`: Optional notes or comments
