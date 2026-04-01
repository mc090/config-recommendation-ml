# Dataset Card

## Motivation
My motivation for creating this dataset is to explore the process of building a custom dataset and to have a dedicated resource for further processing in machine learning models. This work forms the foundation of my thesis. The dataset focuses exclusively on Python repositories, as the primary label of interest (`has_pyproject_toml`) is Python-specific, and restricting to a single language ecosystem ensures feature coherence and avoids language as a trivial confound.

## Intended Use
The primary intended use is to train machine learning models for configuration recommendation systems. The dataset is also suitable for research in software analytics and automated tooling.

## Data Sources and Selection Criteria

- **Sources**: Publicaly available GitHub repositories collected via the GitHub API.
- **Selection Criteria**: Only repositories whose **primary language is Python** (as reported by the GitHub API `language` field) are included. This decision ensures label coherence (particularly for `has_pyproject_toml`), feature relevance, and a well-defined problem scope. Key criteria:

  - **MIN_STARS=10**: Balances quality (filters toy projects) with diversity (retains emerging tools)
  - **Size 10 KB - 500 MB**: Filters trivial repos, prevents timeouts on monorepos
  - **Activity within 365 days**: Focus on current practices in maintained projects
  - **Excludes forks and archived repos**: Standard practice, avoids duplicates

- **Collection Time Estimation**: The pipeline makes approximately 2 API requests per repository (one for branch tree SHA, one for full git tree), plus search pagination requests. Secondary rate limit protection enforces a minimum 1.0s delay between requests to prevent burst-related errors. Time estimation formula:
  ```
  Total requests = ceil(max_repos / 100) + (max_repos × 2)
  Time with primary limits (minutes) = Total requests / requests_per_minute
  Time with secondary limits (minutes) = Total requests / 60  (1.0s delay = max 60 req/min)
  Actual time = max(Time with primary limits, Time with secondary limits)
  ```
  **Examples** (assumes default `MIN_REQUEST_DELAY=1.0s`):
  
  - 100 repos: ~3.5 minutes (201 requests ÷ 60 req/min effective rate)
  - 500 repos: ~17 minutes (1,001 requests ÷ 60 req/min)
  - 1,000 repos: ~34 minutes (2,001 requests ÷ 60 req/min)
  - 5,000 repos: ~168 minutes (10,001 requests ÷ 60 req/min)
  
  Add approximately 10% overhead for network latency and processing.
  
  **Note**: GitHub Search API enforces 30 requests/minute, and secondary rate limits (triggered by request bursts) are mitigated by enforcing minimum delays between requests. The effective rate is limited by the more restrictive constraint (typically secondary limits at 1.0s = 60 req/min).

- **Adaptive Batching for Large Datasets**: GitHub Search API has a hard limit of 1000 results per query. When `MAX_REPOS > 1000`, the pipeline automatically uses greedy star-based batching to bypass this limit. Algorythm steps:
  1. Start downloading repositories with `stars >= MIN_STARS` (sorted descending)
  2. If we reach 1000 results, adjust threshold to continue from the lowest star count in current batch
  3. Continue step 1 and 2 until target count is reached or no more repos available
  
  **Quality guarantee**: Repositories are always collected in descending star order, ensuring the highest-quality projects are prioritized for dataset quality.

## Label Collection vs. Modelling Scope
All configuration file presence labels listed below are collected and stored in the dataset during extraction. However, not all labels are used as targets in ML experiments — the current modelling scope is limited to the three labels marked as primary. Additional collected labels are retained in the dataset as metadata to support future experiments without requiring data re-collection. The subset used for ML training is documented in the [Model Card](./model_card.md).

## Schema

The dataset is stored as a CSV file with one row per repository. Each repository has structural features (file counts, directory counts, etc.), derived metrics (averages, ratios), and multi-label targets (configuration file presence).

> **Test vs. Source Files**: Test files (`num_test_files`) are counted separately from Python source files (`num_py_files`) because testing practices correlate with configuration needs. This separation preserves testing maturity as an independent predictive signal.

### Attributes

> `repo_url` is an identifier/metadata field included for traceability and potential dataset reuse. It must not be used as a model feature.

| Name | Type | Description | Example |
|---|---|---|---|
| `repo_url` | string | Link to the GitHub repository (identifier) | `https://github.com/user/repo` |
| `stars` | int | Number of stars in GitHub repository | `1234` |
| `forks` | int | Number of forks in GitHub repository | `56` |
| `repo_size_kb` | int | Total repository size in kilobytes as reported by the GitHub API | `2048` |
| `open_issues_count` | int | Number of currently open issues | `12` |
| `num_files` | int | Total number of files (all extensions, including test files) | `42` |
| `num_py_files` | int | Number of Python (`.py`) files, excluding test files (test files are counted separately in `num_test_files`) | `12` |
| `num_js_files` | int | Number of JavaScript (`.js`) files | `2` |
| `num_ts_files` | int | Number of TypeScript (`.ts`) files | `0` |
| `num_html_files` | int | Number of HTML (`.html`) files | `1` |
| `num_css_files` | int | Number of CSS (`.css`) files | `0` |
| `num_json_files` | int | Number of JSON (`.json`) files | `3` |
| `num_sh_files` | int | Number of Shell (`.sh`) files | `1` |
| `num_yaml_files` | int | Number of YAML (`.yml` or `.yaml`) files | `3` |
| `num_test_files` | int | Number of Python test files matching `test_*.py` or `*_test.py` patterns anywhere in the repository tree | `5` |
| `test_file_ratio` | float | Ratio of test files to all Python files: `num_test_files / (num_py_files + num_test_files)`. Captures testing investment as a normalised value independent of repo size. `0` when no Python files are present. | `0.29` |
| `num_docs_files` | int | Number of documentation files (`.md` or `.rst`) | `2` |
| `num_notebooks` | int | Number of Jupyter Notebook (`.ipynb`) files | `0` |
| `other_extensions_count` | int | Number of files whose extension is not one of: `.py`, `.js`, `.ts`, `.html`, `.css`, `.json`, `.sh`, `.yml`, `.yaml`, `.md`, `.rst`, `.ipynb` | `4` |
| `has_dedicated_test_dir` | bool | True if any top-level directory is named `tests`, `test`, or `__tests__` | `true` |
| `has_license` | bool | True if a `LICENSE`, `LICENSE.md`, or `LICENSE.txt` file is present at the repository root | `true` |
| `has_src_dir` | bool | True if a top-level directory named `src/` is present. Specifically identifies the src-layout packaging convention; projects using a named package directory are `false` | `true` |
| `has_docs_dir` | bool | True if a top-level directory named `docs/` or `doc/` is present | `false` |
| `has_scripts_dir` | bool | True if a top-level directory named `scripts/` or `bin/` is present | `false` |
| `num_dirs` | int | Total number of directories | `8` |
| `avg_files_per_dir` | float | Average number of files per directory, computed as `num_files / (num_dirs + 1)`. The `+1` accounts for the repository root, ensuring a consistent denominator for all repos including flat ones with no subdirectories. | `5.25` |
| `avg_py_file_len` | float | Average length of Python source files in lines of code, excluding test files. `0` when no `.py` files are present | `200.5` |
| `avg_test_file_len` | float | Average length of Python test files in lines of code. `0` when no test files are present | `85.0` |
| `avg_nb_cell_count` | float | Average number of cells (code + markdown) per Jupyter Notebook file. `0` when no notebooks are present  | `24.75` |
| `avg_docs_file_len` | float | Average length of documentation files in lines. `0` when no documentation files are present | `120.0` |
| `num_dependencies` | int | Number of declared dependencies parsed from `requirements.txt`, `requirements-dev.txt`, `requirements_dev.txt`, `requirements/*.txt` (files in requirements/ directory), `pyproject.toml` (PEP 621 `[project].dependencies` and Poetry `[tool.poetry.dependencies]`, Python itself excluded from Poetry count), `setup.cfg` (`[options].install_requires`), and `Pipfile` (`[packages]` section only; dev dependencies excluded). Counts are summed across all parseable dependency files present. `setup.py` is not parsed (see Limitations). | `10` |
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
| `has_precommit_config` | bool | Presence of `.pre-commit-config.yaml` at the repository root | `false` |
| `has_setup_py` | bool | Presence of `setup.py` at the repository root | `true` |
| `has_tox_ini` | bool | Presence of `tox.ini` at the repository root | `false` |
| `has_makefile` | bool | Presence of `Makefile` at the repository root | `false` |

## Collection and Preprocessing Steps

### Collection
Data is collected via a multi-stage automated pipeline driven by DVC:

1. **pipeline_init** (`src/pipeline_init.py`): Generates timestamped run ID and logs configuration snapshot to `logs/config_<run_id>.json` for reproducibility.

2. **fetch_raw** (`src/data/fetch_raw.py`): Queries GitHub Search API for Python repositories matching configured criteria (stars, size, activity, etc.). For each repository, fetches the full recursive git tree via GitHub Trees API. Includes automatic retry with exponential backoff (up to 5 attempts) for rate limit errors. Secondary rate limit protection enforces minimum 1.0s delay between requests to prevent burst-related 403/429 errors. Output: `data/raw/raw_metadata.json` containing repo metadata + file tree per repository.

3. **extract_structure** (`src/data/extract_structure.py`): Scans the flat file tree to count files by extension, enumerate directories, detect configuration files (labels), and identify structural patterns (src-layout, test directories, etc.). Preserves per-file sizes for later averaging. Output: `data/interim/structure.json`.

4. **enrich_content** (`src/data/enrich_content.py`): Downloads each repository's HEAD tarball (one API call per repo). Reads Python source files, documentation, notebooks, and dependency manifests to compute content-based features: `avg_py_file_len`, `avg_docs_file_len`, `avg_nb_cell_count`, and `num_dependencies`. Output: `data/interim/structure_enriched.json`.

5. **compute_features** (`src/data/compute_features.py`): Computes all remaining derived features including `num_files`, `num_py_files`, `num_test_files`, `num_dirs`, `avg_files_per_dir`, `test_file_ratio`, `repo_age_days`, and `recent_activity_days`. Produces the complete ML feature vector per repository. Output: `data/interim/computed_features.json`.

6. **build_dataset** (`src/data/build_dataset.py`): Loads computed features and saves as complete CSV with version and manifest. Output: `data/processed/v{version}/dataset.csv` + `manifest.json`.

The pipeline is reproducible: each run is linked to a git commit, a config snapshot in `logs/`, and a dataset version with manifest. Re-running `dvc repro` reproduces the entire pipeline from raw data to final splits.

## Limitations
- **Limitations**: The dataset may not represent all types of software projects, as it focuses on repositories with specific characteristics that meets intended selection criteria.
- **`setup.py` only repositories excluded**: Repositories where `setup.py` is the only dependency file are excluded during the `enrich_content` stage (stage 4). Rationale: `setup.py` is arbitrary Python code and cannot be reliably parsed without execution, which poses security risks and reproducibility challenges. Including such repositories would produce `num_dependencies = 0`, which is indistinguishable from a repository that has no dependencies, silently corrupting the feature. **Note**: Repositories with `setup.py` plus other parseable dependency files (e.g., `requirements.txt`, `pyproject.toml`) are **NOT** excluded. Only repos with setup.py as the exclusive dependency file are filtered out.

## Versioning Policy

The pipeline uses semantic versioning (`MAJOR.MINOR.PATCH`) with automatic version management:

- **Default behavior**: When no version is specified, the pipeline scans `data/processed/` for existing versions and auto-increments the patch number (e.g., `1.0.5` → `1.0.6`). If no versions exist, it starts at `1.0.0`.
- **Manual override**: Set `DATASET_VERSION` environment variable for major/minor bumps (e.g., `DATASET_VERSION=2.0.0`). If the specified version already exists, the pipeline increments its patch number until finding an unused version.
- **Isolation**: Each version is stored in an isolated directory (`data/processed/v{version}/`) with both `dataset.csv` and `manifest.json` for full reproducibility.

## Manifest Structure
Each processed dataset version includes a `manifest.json` file recording provenance and reproducibility information. The manifest is automatically generated by `src/data/build_dataset.py`.

**Example manifest:**
```json
{
  "version": "1.0.0",
  "created_at": "2026-03-26T17:59:00.123456+00:00",
  "script": "src/data/build_dataset.py",
  "git_commit": "abc123def456789abcdef123456789abcdef1234",
  "input_source": "data/interim/computed_features.json",
  "pipeline_stats": {
    "extraction_log": "extraction_20260326_175900.log"
  },
  "schema": {
    "total_features": 38,
    "total_rows": 1000,
    "feature_columns": [
      "repo_url",
      "stars",
      "forks",
      "repo_size_kb",
      "open_issues_count",
      "num_files",
      "..."
    ]
  },
  "checksum": "sha256:1a2b3c4d5e6f7890abcdef1234567890abcdef1234567890abcdef1234567890"
}
```

**Field descriptions**:
- `version`: Semantic version of the dataset (X.Y.Z format)
- `created_at`: ISO 8601 timestamp with UTC timezone when dataset was created
- `script`: Path to the script that generated this dataset (always `src/data/build_dataset.py`)
- `git_commit`: Git commit hash of the code used to generate the dataset (for full reproducibility)
- `input_source`: Path to the input data file used to build this dataset (typically `data/interim/computed_features.json`)
- `pipeline_stats`: Optional dictionary containing pipeline execution metadata
  - `extraction_log`: Name of the most recent extraction log file from `logs/` directory
- `schema`: Dataset schema information
  - `total_features`: Total number of feature columns in the CSV
  - `total_rows`: Total number of samples (repositories) in the dataset
  - `feature_columns`: Complete list of all column names in order (useful for schema validation)
- `checksum`: SHA256 checksum of the `dataset.csv` file in format `sha256:<hash>` (for integrity verification)
