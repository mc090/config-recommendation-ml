# Experiment Plan

## Overview
The main goal of these experiments is to develop the most effective machine learning model for recommending configuration files for programming projects. Various ML models will be compared, and different preprocessing methods may also be explored.

## Baselines
- Simple heuristic-based recommendations (e.g., based on project language or structure)
- Most common configuration files in similar repositories

## Metrics
- Accuracy
- Precision, Recall, F1-score

## Cross-Validation Strategy
- Stratified K-Fold (k=5), stratified by project language or project-size bucket
- Ensure balanced representation of project types in each fold

## Hyperparameter Tuning Plan
- Grid search or randomized search for key model parameters
- Use validation set from cross-validation splits

## Logging and Artifact Policy
- Log all experiment runs, parameters, and results using MLflow or similar tool (TBA)
- Save model checkpoints and configuration files for each run

## Seeds
Default seeds location is [Seeds file](../config/seeds.yaml).

## Statistical Testing Approach
TBA

## Compute Budget
- Experiments will be run on local machine with NVIDIA RTX 2060 GPU.

## Workflow Conventions

The project uses the **Dev Container** as the canonical development environment. It enforces a reproducible setup automatically (GPU passthrough, pre-commit hooks, correct dependencies) and eliminates environment drift between machines. Local Conda setup is available as a fallback only.

The **data pipeline** (`fetch_raw` → `extract_structure` → `compute_features` → `build_dataset`) is driven by `dvc repro`. DVC handles stage caching and dependency tracking, ensuring that only changed stages re-run and that each processed snapshot is traceable. Manual script execution is reserved for debugging individual stages.

**Notebooks** are used exclusively for exploratory analysis, visualization, and thesis figures. Final training runs are executed via CLI scripts logged with MLflow, making each run independently referenceable by commit hash, config, and dataset manifest.

## Pipeline Stage Summary

| Stage | Script | Input | Output | Responsibility |
|---|---|---|---|---|
| `fetch_raw` | `src/data/fetch_raw.py` | GitHub API + config | `data/raw/raw_metadata.json` | Query GitHub Search API per language; fetch full recursive git tree per repo. Each record: `{"repo": <API item>, "tree": {"tree": [{"path":…, "type":…, "size":…}]}}` |
| `extract_structure` | `src/data/extract_structure.py` | `raw_metadata.json` | `data/interim/structure.json` | Scan the flat tree to count files by extension, list directories, detect label targets (`has_pyproject_toml`, `has_dockerfile`, `has_github_actions`), and preserve per-file sizes for averaging. No derived math yet. |
| `compute_features` | `src/data/compute_features.py` | `structure.json` | `data/interim/features.json` | Compute all derived numeric features: `avg_files_per_dir`, `avg_py_file_len`, `avg_docs_file_len`, `repo_age_days`, `recent_activity_days`, `num_dependencies`, etc. Output is the full ML feature vector per repo, including labels. |
| `build_dataset` | `src/data/build_dataset.py` | `features.json` | `data/processed/dataset.csv` + `manifest.json` | Stratified train/val/test split (70/15/15), serialise to CSV with a `split` column, write `manifest.json` with version, git commit, row count, and SHA-256 checksum. |

## Mapping to Scripts/Notebooks
- [Pipeline init](../src/pipeline_init.py)
- [Data collection](../src/data/fetch_raw.py)
- Structure extraction — `src/data/extract_structure.py` (TBA)
- Feature computation — `src/data/compute_features.py` (TBA)
- Dataset build — `src/data/build_dataset.py` (TBA)
- [Exploration](../notebooks/01_explore_dataset.ipynb)
- Model training/evaluation (TBA)

## Reproducibility Steps
1. Clone the repository and set up the environment as described in the [README](../README.md).
2. Prepare the dataset using provided scripts and configuration files.
3. Run experiments using the specified scripts/notebooks and configuration YAMLs.
4. Save and reference the reproducibility snapshot (commit hash, manifest, configs, environment files) for each experiment.

## Timeline & Milestones
- To be announced (TBA)
