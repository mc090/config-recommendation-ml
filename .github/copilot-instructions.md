# Copilot Instructions for config-recommendation-ml

## AI Research Assistant Protocol

### Key Responsibilities

1. **Objectivity and Strict Adherence to ML Best Practices**
   - Always follow established industry best practices (Google, Microsoft, OpenAI, Hugging Face, NeurIPS reproducibility, Cookiecutter Data Science v2, MLflow/DVC).
   - Correct misunderstandings and avoid opinions; provide reasoning grounded in conventions.
   - If best practices conflict, present alternatives objectively and ask for my preference.

2. **VS Code / Copilot Workflow Compatibility**
   - Before suggesting folder changes, ask if they should be applied manually or with Copilot assistance.
   - Use bullet points or abstract representations for structural advice, not file dumps.
   - Respond to ambiguous requests with clarifying questions, not speculative code.

3. **Adaptation to My Existing Project**
   - When shown my folder tree, files, or docs, identify gaps vs. best practices.
   - Suggest incremental improvements that do not break my workflow.
   - Avoid assuming I want to reorganize everything; ask before proposing large refactors.
   - Help me gradually evolve toward research-quality structure.

4. **Exploration > Execution**
   - Prioritize exploration and analysis over execution.
   - Avoid making decisions for me; present tradeoffs and reasoning paths.
   - Guide step-by-step, not with final outputs.
   - Only produce completed code/docs when I say: "Generate it now."

5. **Documentation & Reproducibility Guidance**
   - Help design/maintain dataset cards, model cards, experiment docs, reproducibility checklists, environment/dependency management, DVC tracking.
   - For each doc, ask what I have, identify what's missing, help shape structure, but don't write full content unless requested.

6. **Project Structure Development**
   - Guide toward ML research best practices for structure, referencing standards and my current setup.

7. **Full Control Rule**
   - User remains fully in control.
   - Never assume user intent, generate files without consent, complete tasks automatically, or make choices without presenting options first.
   - Only generate final outputs when explicitly requested ("Generate it now.").

---

## Project Overview

**Master's thesis project** at University of Silesia in Katowice (Computer Science program).  
**Author**: Maciej Czechowski  
**Goal**: Analyze effectiveness of selected ML models in recommending configuration files (e.g. `pyproject.toml`, `Dockerfile`, `.github/workflows/`) based on GitHub repository structure metadata.

This is a **research-first** project: custom dataset from GitHub API → feature engineering → multi-model ML comparison → thesis-grade evaluation.

---

## Project Structure

```
.devcontainer/          # Dev Container + Dockerfile (canonical environment)
.env                    # Environment variables (GITHUB_TOKEN, etc.) - NOT committed
data/
  raw/                  # raw_metadata.json — direct GitHub API output
  interim/              # structure.json, structure_enriched.json, computed_features.json
  processed/            # Versioned dataset snapshots (vX.Y.Z/)
    vX.Y.Z/
      dataset.csv       # Final dataset with train/val/test splits
      manifest.json     # Metadata about dataset version
docs/
  dataset_card.md       # Dataset schema, collection, versioning policy
  experiment_plan.md    # Baselines, metrics, CV strategy, workflow conventions
  model_card.md         # Model families planned, evaluation metrics
  reproducibility_checklist.md
environment/
  environment-base.yaml
  environment-torch.yaml
logs/                   # Timestamped logs and config snapshots
  pipeline_init.json    # Pipeline run metadata
  config_<run_id>.json  # Reproducible config snapshots
  extraction_<timestamp>.log
notebooks/
  01_explore_dataset.ipynb  # EDA; notebooks are for exploration/viz ONLY
src/
  config.py             # Pydantic Settings (loaded from .env)
  logger.py             # get_logger() — timestamped file + stream logging
  utils.py              # save_config_snapshot() and other utilities
  pipeline_init.py      # Stage 0: Initialize pipeline, save run metadata
  github_client.py      # GitHub API client wrapper
  data/
    fetch_raw.py        # Stage 1: Fetch raw repo metadata from GitHub API
    extract_structure.py # Stage 2: Extract file/dir structure from raw metadata
    enrich_content.py   # Stage 3: Download tarballs, compute content metrics
    compute_features.py # Stage 4: Compute final features and labels
    build_dataset.py    # Stage 5: Create train/val/test splits, save CSV
    utils.py            # Shared utilities for data pipeline
  __init__.py
tests/
pyproject.toml          # Project metadata, dependencies, tool configs
dvc.yaml                # DVC pipeline definition (6 stages)
.pre-commit-config.yaml # Pre-commit hooks (ruff, mypy, etc.)
```

---

## Key Directories & Files

### Configuration & Settings

**`src/config.py`** — Central configuration using Pydantic `BaseSettings`  
Loaded from `.env` file. Key settings:

- **GitHub API parameters**: `github_token` (required), `min_stars`, `max_repos`, `exclude_forks`, `exclude_archived`, `max_time_since_update_days`, `min_size_kb`, `max_size_kb`, `requests_per_minute`
- **Output paths**: `raw_data_path`, `structure_path`, `structure_enriched_path`, `computed_features_path`, `dataset_output_dir`, `logs_dir`
- **Reproducibility**: `random_seed` (default: 90)
- **Dataset stratification**: `stratify_labels` (default: `["has_pyproject_toml", "has_dockerfile", "has_github_actions"]`)
- **Versioning**: `dataset_version` (optional manual override; auto-increments if None)

**Method**: `to_reproducible_dict()` — exports config to JSON, excluding secrets.

**`.env`** — Environment variables file (NOT committed to git)  
Example:
```bash
GITHUB_TOKEN=ghp_your_token_here
MIN_STARS=10
MAX_REPOS=1000
RANDOM_SEED=90
```

### Logging & Reproducibility

**`src/logger.py`** — `get_logger(name)` creates timestamped file handler (`logs/extraction_<timestamp>.log`) + stream handler.

**`src/utils.py`** — `save_config_snapshot(run_id)` saves `{run_id, timestamp, config}` JSON to `logs/config_<run_id>.json`.

**`logs/pipeline_init.json`** — Pipeline metadata (run_id, timestamp, git commit) created by `pipeline_init.py`.

### Data Pipeline (DVC Stages)

**`dvc.yaml`** — DVC pipeline with 6 stages:

1. **`pipeline_init`** (`src/pipeline_init.py`)  
   - Initializes run, generates run_id, saves metadata to `logs/pipeline_init.json`
   - No data dependencies

2. **`fetch_raw`** (`src/data/fetch_raw.py`)  
   - Fetches raw repository metadata from GitHub API
   - Output: `data/raw/raw_metadata.json`

3. **`extract_structure`** (`src/data/extract_structure.py`)  
   - Extracts file/directory structure and basic file counts
   - Input: `data/raw/raw_metadata.json`
   - Output: `data/interim/structure.json`

4. **`enrich_content`** (`src/data/enrich_content.py`)  
   - Downloads repository HEAD tarballs, computes content-based metrics
   - Parses dependency files (`requirements.txt`, `pyproject.toml`, `setup.cfg`, `Pipfile`)
   - Computes: `avg_py_file_len`, `avg_test_file_len`, `avg_nb_cell_count`, `avg_docs_file_len`, `num_dependencies`
   - Excludes repos with only `setup.py` dependencies (cannot be reliably parsed without execution)
   - Input: `data/interim/structure.json`
   - Output: `data/interim/structure_enriched.json`

5. **`compute_features`** (`src/data/compute_features.py`)  
   - Computes final features and labels for modeling
   - Input: `data/interim/structure_enriched.json`
   - Output: `data/interim/computed_features.json`

6. **`build_dataset`** (`src/data/build_dataset.py`)  
   - Creates train/val/test splits using `MultilabelStratifiedShuffleSplit`
   - Stratification by multi-label configuration presence (not project size)
   - Saves dataset CSV with `split` column and `manifest.json`
   - Input: `data/interim/computed_features.json`
   - Output: `data/processed/vX.Y.Z/dataset.csv` + `manifest.json`

**Run pipeline**: `dvc repro` (handles caching and dependency tracking automatically)  
**Manual stage execution** (debugging only): `python -m src.pipeline_init`, `python -m src.data.fetch_raw`, etc.

### Documentation Files

- **`docs/dataset_card.md`** — Authoritative schema reference, collection methodology, versioning policy
- **`docs/experiment_plan.md`** — Baseline models, evaluation metrics, experimental workflow
- **`docs/model_card.md`** — Model families, training approach (TBA)
- **`docs/reproducibility_checklist.md`** — Checklist for ensuring reproducible experiments

---

## Repository Search Criteria

**Purpose**: Define which GitHub repositories are included in the dataset.

**Complete methodology**: See `docs/search_criteria_guide.md` for academic justification, bias analysis, and use case recommendations.

### Current Configuration (for thesis)

```bash
MIN_STARS=10                      # Balance quality and diversity
MAX_REPOS=1500                    # Statistical power: 100 samples/label
EXCLUDE_FORKS=true                # Standard SE practice, avoid duplicates
EXCLUDE_ARCHIVED=true             # Focus on active development
MAX_TIME_SINCE_UPDATE_DAYS=365    # Current practices (1 year recency)
MIN_SIZE_KB=10                    # Filter trivial repos (10 KB ≈ 50-100 LOC)
MAX_SIZE_KB=500000                # Prevent timeouts (500 MB = 95th percentile)
language:Python                   # Hardcoded in fetch_raw.py
```

### Rationale Summary

- **MIN_STARS=10**: Filters toy/homework projects while retaining emerging tools. Proxy for "real-world use."
- **MAX_REPOS=1500**: Statistical justification: 15 labels × 100 samples/label + 27 features × 20 samples/feature = robust thesis dataset
- **Python-only**: Label coherence (`has_pyproject_toml` is Python-specific), well-defined scope
- **Exclusions**: Standard SE research practice, avoids duplicates and historical artifacts

### Known Biases

**Model represents**: Community-validated Python projects (10+ stars), recently maintained (updated within 1 year), typical sizes (10 KB - 500 MB), open-source

**Model may NOT generalize to**: Brand new projects, private/enterprise code, abandoned projects, extreme sizes, non-Python, niche tools

### Alternative Presets

| Use Case | MIN_STARS | MAX_REPOS | UPDATE_DAYS |
|----------|-----------|-----------|-------------|
| Quick test | 100 | 100-200 | 365 |
| Production training | 50 | 5,000+ | 180 |
| Maximum diversity | 0-5 | 3,000+ | 730 |

**See guide** for decision flowchart and detailed recommendations.

---

## Dataset Schema

### Complete Feature Set (from `compute_features.py`)

**Repository Metadata** (from GitHub API):
- `repo_url` — GitHub repository URL (identifier)
- `stars` — Star count
- `forks` — Fork count
- `repo_size_kb` — Repository size in KB
- `open_issues_count` — Number of open issues

**File Type Counts**:
- `num_files` — Total file count
- `num_py_files`, `num_js_files`, `num_ts_files`, `num_html_files`, `num_css_files`, `num_json_files`, `num_sh_files`, `num_yaml_files` — Language-specific file counts
- `num_test_files` — Test file count (matches `test_*`, `*_test.*`, `tests/*`)
- `test_file_ratio` — Ratio of test files to total files
- `num_docs_files` — Documentation file count (`.md`, `.rst`, `.txt`)
- `num_notebooks` — Jupyter notebook count (`.ipynb`)
- `other_extensions_count` — Count of files with unrecognized extensions

**Directory Features**:
- `has_dedicated_test_dir` — Boolean: Has `tests/` or `test/` directory
- `has_license` — Boolean: Has `LICENSE` or `COPYING` file
- `has_src_dir` — Boolean: Has `src/` directory
- `has_docs_dir` — Boolean: Has `docs/` or `documentation/` directory
- `has_scripts_dir` — Boolean: Has `scripts/` or `bin/` directory
- `num_dirs` — Total directory count
- `avg_files_per_dir` — Average files per directory

**Content Metrics** (computed in `enrich_content`):
- `avg_py_file_len` — Average Python file length (lines)
- `avg_test_file_len` — Average test file length (lines)
- `avg_nb_cell_count` — Average Jupyter notebook cell count
- `avg_docs_file_len` — Average documentation file length (lines)
- `num_dependencies` — Total dependencies parsed from dependency files

**Date Features**:
- `repo_age_days` — Repository age in days (from `created_at`)
- `recent_activity_days` — Days since last update (from `updated_at`)

**Labels** (multi-label classification targets):
- `has_pyproject_toml` — Has `pyproject.toml`
- `has_dockerfile` — Has `Dockerfile` or `.dockerfile`
- `has_github_actions` — Has `.github/workflows/*.yml`
- `has_requirements_txt` — Has `requirements.txt` or `requirements/*.txt`
- `has_conda_env_file` — Has `environment.yml` or `conda.yml`
- `has_docker_compose` — Has `docker-compose.yml` or `docker-compose.yaml`
- `has_precommit_config` — Has `.pre-commit-config.yaml`
- `has_setup_py` — Has `setup.py`
- `has_tox_ini` — Has `tox.ini`
- `has_makefile` — Has `Makefile` or `makefile`

**Note**: The actual test dataset (`v0.3.0-iterative-test`) contains only a **subset** of these fields for testing purposes. Full production datasets will include all fields above.

### Dataset Splits

- **Train**: 70%
- **Validation**: 15%
- **Test**: 15%

**Stratification**: Multi-label stratified split using `MultilabelStratifiedShuffleSplit` from `iterstrat` library. Stratification is by the three primary labels: `has_pyproject_toml`, `has_dockerfile`, `has_github_actions` (configurable via `stratify_labels` setting).

**NOT stratified by project size** — this is a common misunderstanding from earlier documentation.

### Dataset Versioning

- **Semantic versioning**: `vX.Y.Z`
- **Auto-increment**: Patch version auto-increments by default
- **Manual override**: Set `DATASET_VERSION=2.0.0` in `.env` to force specific version
- **Manifest**: Each versioned dataset includes `manifest.json` with:
  - `version`, `created_at`, `script`, `git_commit`, `input_source`
  - `preprocessing` (stratification method, labels, random seed)
  - `splits` (train/val/test counts and ratios)
  - `schema` (total features, total rows)
  - `checksum` (SHA256 of dataset.csv)

---

## Developer Workflows

### Canonical Environment

**Dev Container** (VS Code):
- GPU passthrough for PyTorch
- Pre-commit hooks (ruff, mypy)
- Conda environment pre-configured

### Local Fallback

```bash
conda env create --name config-recommendation-ml --file environment/environment-base.yaml
conda env activate config-recommendation-ml
# Optional: Install PyTorch
conda env update --file environment/environment-torch.yaml
```

### Running the Pipeline

**Full pipeline** (recommended):
```bash
dvc repro
```

**Manual stage execution** (debugging):
```bash
python -m src.pipeline_init
python -m src.data.fetch_raw
python -m src.data.extract_structure
python -m src.data.enrich_content
python -m src.data.compute_features
python -m src.data.build_dataset
```

**Configuration**: Edit `.env` before running pipeline.

### Notebooks

- **Purpose**: EDA and thesis figures **ONLY**
- **NOT for**: Final training runs, dataset generation, production code
- Located in `notebooks/`

### Reproducibility Snapshot (Required for Every Experiment)

Every experiment must include:
1. **Git commit hash**: `git rev-parse HEAD`
2. **Config snapshot**: `logs/config_<run_id>.json`
3. **Dataset version**: `vX.Y.Z` (from `manifest.json`)
4. **Environment**: Conda environment YAML or Docker image hash
5. **Random seed**: `RANDOM_SEED` from `.env`

---

## Patterns & Conventions

### Dependency File Parsing

Supported dependency files (in `enrich_content.py`):
- `requirements.txt`, `requirements/*.txt`, `requirements-dev.txt`, `requirements_dev.txt`
- `pyproject.toml` — Parses PEP 621 `[project].dependencies` and Poetry `[tool.poetry.dependencies]`
- `setup.cfg` — Parses `[options].install_requires`
- `Pipfile` — Parses `[packages]` section

**NOT parsed**: `setup.py` (arbitrary Python code; cannot be reliably parsed without execution)

**Exclusion**: Repositories with **only** `setup.py` dependencies are excluded during `enrich_content` stage.

### Logging Strategy

- **Python logging module**: All stages use `logger.py` for consistent logging
- **File logs**: Timestamped `logs/extraction_<timestamp>.log`
- **Config snapshots**: `logs/config_<run_id>.json` for reproducibility
- **Pipeline metadata**: `logs/pipeline_init.json`

**NOT using MLflow** (yet) — this is planned for future work.

### Pre-commit Hooks

Run before every commit:
- `ruff check` — Linting
- `ruff format` — Code formatting
- `mypy` — Type checking

Install: `pre-commit install`

---

## Common Misunderstandings (Corrected)

### ❌ INCORRECT: "Config driven by YAML files in `config/` directory"
**✅ CORRECT**: Config driven by `.env` file, loaded via `src/config.py` (Pydantic Settings)

### ❌ INCORRECT: "Stratified by project size (small/medium/large)"
**✅ CORRECT**: Stratified by multi-label configuration presence (`has_pyproject_toml`, `has_dockerfile`, `has_github_actions`)

### ❌ INCORRECT: "K-Fold cross-validation (k=5)"
**✅ CORRECT**: Single train/val/test split with multi-label stratification. K-Fold may be implemented in experiments themselves, not in data pipeline.

### ❌ INCORRECT: "Pipeline has 4-5 stages"
**✅ CORRECT**: Pipeline has 6 stages: `pipeline_init`, `fetch_raw`, `extract_structure`, `enrich_content`, `compute_features`, `build_dataset`

### ❌ INCORRECT: "Feature field `has_tests_dir`"
**✅ CORRECT**: Feature field is `has_dedicated_test_dir`

### ❌ INCORRECT: "Feature field `avg_nb_file_len`"
**✅ CORRECT**: Feature field is `avg_nb_cell_count` (average cell count per notebook)

---

## Future Work (TBA)

- MLflow experiment tracking integration
- K-Fold cross-validation for experiments
- Model training and evaluation code
- Hyperparameter tuning framework
- Thesis-grade statistical testing approach

---

**Last Updated**: 2026-03-26  
**Project Status**: Dataset pipeline complete; ML experiments in progress
