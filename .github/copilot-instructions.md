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
  - Only produce completed code/docs when I say: “Generate it now.”

5. **Documentation & Reproducibility Guidance**
  - Help design/maintain dataset cards, model cards, experiment docs, reproducibility checklists, environment/dependency management, YAML configs, MLflow/DVC tracking.www
  - For each doc, ask what I have, identify what’s missing, help shape structure, but don’t write full content unless requested.

6. **Project Structure Development**
  - Guide toward ML research best practices for structure, referencing standards and my current setup.

  7. **Full Control Rule**
  - User remain fully in control.
  - Never assume user intent, generate files without consent, complete tasks automatically, or make choices without presenting options first.
  - Only generate final outputs when explicitly requested ("Generate it now.").


## Project Overview

**Master's thesis project** at University of Silesia in Katowice (Computer Science program).  
**Author**: Maciej Czechowski  
**Goal**: Analyse effectiveness of selected ML models in recommending configuration files (e.g. `pyproject.toml`, `Dockerfile`, `.github/workflows/`) based on GitHub repository structure metadata.

This is a **research-first** project: custom dataset from GitHub API → feature engineering → multi-model ML comparison → thesis-grade evaluation.

---

## Project Structure

```
.devcontainer/          # Dev Container + Dockerfile (canonical environment)
config/                 # YAML configs: data.yaml, features.yaml, training.yaml, seeds.yaml
data/
  raw/                  # raw_metadata.json — direct GitHub API output
  interim/              # structure.json, features.json — intermediate pipeline artifacts
  processed/            # dataset.csv + manifest.json per versioned snapshot
docs/
  dataset_card.md       # schema, collection, versioning policy, manifest template
  experiment_plan.md    # baselines, metrics, CV strategy, workflow conventions
  model_card.md         # model families planned, evaluation metrics
  reproducibility_checklist.md
environment/
  environment-base.yaml
  environment-torch.yaml
logs/                   # per-run extraction logs and configs (extraction_YYYYMMDD_HHMMSS.log)
notebooks/
  01_explore_dataset.ipynb  # EDA; notebooks are for exploration/viz ONLY
src/
  config.py             # Pydantic Settings (env: .env → GITHUB_TOKEN etc.)
  logger.py             # get_logger() — writes to logs/ with timestamped filename
  utils.py              # save_config_snapshot() — saves reproducible run config to logs/
  fetch_raw.py          # Stage 1: fetch raw repo metadata from GitHub API
  extract_structure.py  # Stage 2: extract file/dir structure features from raw metadata
  compute_features.py   # Stage 3: compute derived features (avg_files_per_dir, etc.)
  extract_dataset.py    # Orchestrator: logs run_id, saves config snapshot, calls pipeline
  __init__.py
tests/
```

---

## Key Directories & Files

- `src/config.py` — Central `Settings` (Pydantic BaseSettings). Reads from `.env`. Fields: `github_token`, `min_stars`, `max_repos`, `languages`, `exclude_forks`, `exclude_archived`, `max_time_since_update_days`, `min_size_kb`, `max_size_kb`, `requests_per_minute`, `data_dir`, `logs_dir`, `random_seed`, `config_snapshot_dir`. Method `to_reproducible_dict()` strips secrets for logging.
- `src/logger.py` — `get_logger(name)`: creates a timestamped file handler under `logs/` + stream handler.
- `src/utils.py` — `save_config_snapshot(run_id)`: saves `{run_id, timestamp, config}` JSON to `logs/config_<run_id>.json`.
- `dvc.yaml` — DVC pipeline: `fetch_raw` → `extract_structure` → `compute_features` → `build_dataset`. Run with `dvc repro`.
- `config/` — YAML files drive all pipeline behaviour. `seeds.yaml` holds `data_seed` and `sampling_seed` for reproducibility.
- `docs/dataset_card.md` — Authoritative schema reference. See "Attributes" and "Labels" tables.

---

## Dataset Schema (from dataset_card.md)

**Features (attributes):**
`repo_url`, `stars`, `forks`, `created_at`, `last_updated`, `num_files`, `num_py_files`, `num_js_files`, `num_ts_files`, `num_html_files`, `num_css_files`, `num_json_files`, `num_sh_files`, `num_test_files`, `num_docs_files`, `num_notebooks`, `other_extensions_count`, `has_tests_dir`, `num_dirs`, `top_level_dirs`, `avg_files_per_dir`, `avg_py_file_len`, `avg_nb_file_len`, `avg_docs_file_len`, `num_dependencies`, `repo_age_days`, `recent_activity_days`

**Labels (multi-label classification targets):**
`has_pyproject_toml`, `has_dockerfile`, `has_github_actions`

**Splits**: Train 70% / Val 15% / Test 15% — stratified by project language or size bucket.  
**Versioning**: Semantic versioning (`vX.Y.Z`). Each processed snapshot must include a `manifest.json`.

---

## Developer Workflows

- **Canonical environment**: VS Code Dev Container (GPU passthrough, pre-commit hooks, Conda).
- **Local fallback**: `conda env create --name config-recommendation-ml --file environment/environment-base.yaml --file environment/environment-torch.yaml`
- **Run pipeline**: `dvc repro` (handles caching and dependency tracking automatically).
- **Manual stage execution** (debugging only): `python -m src.fetch_raw`, `python -m src.extract_structure`, etc.
- **Config changes**: Edit YAML files in `config/` before re-running pipeline stages.
- **Notebooks**: EDA and thesis figures only — never final training runs.
- **Final training runs**: Via CLI scripts, logged with MLflow, referenced by commit hash + manifest + config.

---

## Patterns & Conventions

- **Reproducibility snapshot** required for every experiment:
  ```
  commit: <git-hash>
  dataset_manifest: data/processed/vX.Y.Z/manifest.json
  configs: [config/data.yaml, config/features.yaml, config/training.yaml]
  environment: [environment/environment-base.yaml, environment/environment-torch.yaml]
  ```
- **Manifest template** (saved as `data/processed/vX.Y.Z/manifest.json`): `version`, `created_at`, `script`, `git_commit`, `preprocessing`, `rows`, `checksum`, `notes`.
- **Random seeds**: always sourced from `config/seeds.yaml` (`data_seed`, `sampling_seed`). Never hardcode seeds in scripts.
- **Secrets**: `GITHUB_TOKEN` lives in `.env` only — never in code or configs. `to_reproducible_dict()` strips it before logging.
- **Linting/formatting**: Ruff (`line-length=88`, Python 3.11+, rules E/F/B/I). Pre-commit hooks enforce this.
- **Logging**: Use `get_logger(__name__)` from `src/logger.py`. Logs go to `logs/extraction_<timestamp>.log`.
- **Config snapshots**: Every extraction run saves a JSON snapshot via `save_config_snapshot(run_id)` to `data/raw/`.
- **No large code blocks** unless user says "Generate it now."
- **No full file rewrites** unless user explicitly requests.

---

## Planned ML Models (from model_card.md)

Decision Trees, Random Forest, Gradient Boosting, SVM, Neural Networks.  
**Evaluation metrics**: Accuracy, Precision, Recall, F1-score.  
**CV strategy**: Stratified K-Fold (k=5), stratified by language or project-size bucket.  
**Hyperparameter tuning**: Grid search or randomized search.  
**Experiment tracking**: MLflow (TBA).  
**Compute**: Local NVIDIA RTX 2060.

---

## Integration Points

- **GitHub API** → `fetch_raw.py` (rate-limited via `requests_per_minute` setting)
- **DVC** → pipeline orchestration and artifact caching (`dvc repro`)
- **MLflow** → experiment tracking (planned, not yet implemented)
- **Pydantic Settings** → config validation and environment loading
- **Ruff** → linting and formatting (via pre-commit)

---

## References

- [README](../README.md)
- [Dataset card](../docs/dataset_card.md)
- [Experiment plan](../docs/experiment_plan.md)
- [Model card](../docs/model_card.md)
- [Reproducibility checklist](../docs/reproducibility_checklist.md)

*Update this file as project conventions evolve. Focus on actionable, codebase-specific guidance for AI agents.*
