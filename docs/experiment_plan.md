# Experiment Plan

## Overview
The main goal of these experiments is to develop the most effective machine learning model for recommending configuration files for programming projects. Various ML models will be compared, and different preprocessing methods may also be explored.

## Current Preparation Milestone (Implemented First)

Before split/CV and model training, generate feature-pruned dataset variants with a CLI-first workflow:

- Run:
  ```bash
  python -m src.experiments.build_variants
  ```
- Variants are saved under the latest dataset version:
  - `variants/original`
  - `variants/corr_070`
  - `variants/corr_060`
  - `variants/dist_expert`
  - `variants/dom_<threshold>` (e.g. `dom_090`)
- Locked preprocessing rules for this phase:
  - Correlation pruning significance: `p < 0.05`
  - Dominance-ratio threshold: `0.90`
  - Expert removals: `avg_files_per_dir`, `avg_nb_cell_count`, `has_license`
- Notebook support for reproducibility/statistics:
  - `notebooks/05_variant_generation_process.ipynb`
  - `notebooks/06_variant_statistics.ipynb`

## Baselines
- Simple heuristic-based recommendations (e.g., based on repository size or structure patterns)
- Most common configuration files in similar Python repositories

## Dataset Splitting Strategy

**The dataset CSV contains unsplit data.** Splitting into train/val/test sets should be performed in experiment scripts, not during dataset building. This provides maximum flexibility for experimentation and follows best practices for academic research.

### Recommended Approach:

1. **Test Set Holdout** (15-20%): Create once at the beginning of experiments using **multi-label iterative stratification** (`MultilabelStratifiedShuffleSplit` from `iterstrat` library) stratified by `has_pyproject_toml`, `has_dockerfile`, `has_github_actions`. Save test indices in experiment logs for consistency.

2. **K-Fold Cross-Validation** (k=5 or k=10): Perform on the remaining training data using `StratifiedKFold` or `MultilabelStratifiedKFold`. Report mean ± std across folds for robust evaluation.

3. **Final Evaluation**: After selecting the best model based on CV results, retrain on the full training set and evaluate once on the holdout test set for final thesis results.

### Why This Approach:
- **Data efficiency**: Uses 100% of training data across folds (vs. fixed 70% in pre-split)
- **Robust estimates**: Mean ± std more reliable than single number
- **Flexibility**: Easy to experiment with different split ratios or stratification strategies
- **Standard practice**: Expected in academic ML research and thesis work

## Cross-Validation Strategy (Implementation)

**In experiment scripts** (not in data pipeline):
- Use `MultilabelStratifiedShuffleSplit` for initial test holdout
- Use `StratifiedKFold` (k=5) or `MultilabelStratifiedKFold` (k=5) for CV
- Stratify by multi-label configuration presence (not project size)
- Track all random seeds and split indices in MLflow/logs

## Metrics
- Accuracy
- Precision, Recall, F1-score (per label and macro/micro averages for multi-label)
- Report as mean ± std across CV folds

## Hyperparameter Tuning Plan
- Grid search or randomized search for key model parameters
- Use validation set from cross-validation splits

## Logging and Artifact Policy

**Current Implementation**:
- **Python logging module**: All pipeline stages use timestamped file logging (`logs/extraction_<timestamp>.log`)
- **Config snapshots**: Reproducible JSON snapshots saved to `logs/config_<run_id>.json` (secrets excluded)
- **Pipeline metadata**: `logs/pipeline_init.json` tracks run_id, timestamp, git commit
- **Dataset manifests**: Each dataset version includes `manifest.json` with version, git commit, checksum

**Future Work**:
- MLflow integration for model training experiments (TBA)
- Track hyperparameters, metrics, and model artifacts
- Enable experiment comparison and model registry

**Reproducibility**: Every pipeline run produces:
1. Timestamped log file with all INFO/WARNING/ERROR messages
2. Config snapshot with all settings (excluding secrets)
3. Git commit hash recorded in manifest

## Seeds
Random seeds (`random_seed`) are configured via `.env` and read by `src/config.py`. The active seed value is captured automatically in `logs/config_<run_id>.json` for every pipeline run.

## Statistical Testing Approach
TBA

## Compute Budget
- Experiments will be run on local machine with NVIDIA RTX 2060 GPU.

## Workflow Conventions

The project uses the **Dev Container** as the canonical development environment. It enforces a reproducible setup automatically (GPU passthrough, pre-commit hooks, correct dependencies) and eliminates environment drift between machines. Local Conda setup is available as a fallback only.

The **data pipeline** (`pipeline_init` → `fetch_raw` → `extract_structure` → `enrich_content` → `compute_features` → `build_dataset`) is driven by `dvc repro`. DVC handles stage caching and dependency tracking, ensuring that only changed stages re-run and that each processed snapshot is traceable. Manual script execution is reserved for debugging individual stages.

**Notebooks** are used exclusively for exploratory analysis, visualization, and thesis figures. Final training runs are executed via CLI scripts logged with MLflow, making each run independently referenceable by commit hash, config, and dataset manifest.

## Pipeline Stage Summary

| Stage | Script | Input | Output | Responsibility |
|---|---|---|---|---|
| `pipeline_init` | `src/pipeline_init.py` | config (`.env`) | `logs/pipeline_init.json` | Generate a timestamped `run_id`, log all config settings (excluding secrets), save `logs/config_<run_id>.json` snapshot, and write `logs/pipeline_init.json` so downstream DVC stages depend on this step. |
| `fetch_raw` | `src/data/fetch_raw.py` | GitHub API + config | `data/raw/raw_metadata.json` | Query GitHub Search API per language; fetch full recursive git tree per repo. Each record: `{"repo": <API item>, "tree": {"tree": [{"path":…, "type":…, "size":…}]}}` |
| `extract_structure` | `src/data/extract_structure.py` | `raw_metadata.json` | `data/interim/structure.json` | Scan the flat tree to count files by extension, list directories, detect label targets (`has_pyproject_toml`, `has_dockerfile`, `has_github_actions`), detect boolean structural flags (`has_dedicated_test_dir`, `has_license`, `has_src_dir`, `has_docs_dir`, `has_scripts_dir`), and preserve per-file sizes for averaging. No derived math yet. |
| `enrich_content` | `src/data/enrich_content.py` | `structure.json` | `data/interim/structure_enriched.json` | Download each repo's HEAD tarball (1 API call per repo; transfer served from GitHub CDN). Reads all Python, documentation, notebook, and dependency files locally. Computes `avg_py_file_len`, `avg_docs_file_len`, `avg_nb_cell_count`, and `num_dependencies` per repo. |
| `compute_features` | `src/data/compute_features.py` | `structure_enriched.json` | `data/interim/features.json` | Compute all remaining derived numeric features: `num_files`, `num_py_files`, `num_test_files`, `num_dirs`, `avg_files_per_dir`, `test_file_ratio`, `repo_age_days`, `recent_activity_days`, etc. Output is the full ML feature vector per repo, including labels. |
| `build_dataset` | `src/data/build_dataset.py` | `computed_features.json` | `data/processed/v{version}/dataset.csv` + `manifest.json` | Load computed features and save as complete unsplit CSV with version and manifest. No pre-splitting performed—splitting should be done in experiment scripts using iterative stratification for multi-label problems. |

## Mapping to Scripts/Notebooks
- [Pipeline init](../src/pipeline_init.py)
- [Data collection](../src/data/fetch_raw.py)
- [Structure extraction](../src/data/extract_structure.py)
- [Content enrichment](../src/data/enrich_content.py)
- [Feature computation](../src/data/compute_features.py)
- [Dataset build](../src/data/build_dataset.py)
- [Exploration](../notebooks/01_explore_dataset.ipynb)
- Model training/evaluation (TBA)

## Reproducibility Steps
1. Clone the repository and set up the environment as described in the [README](../README.md).
2. Prepare the dataset using provided scripts and configuration files.
3. Run experiments using the specified scripts/notebooks and configuration YAMLs.
4. Save and reference the reproducibility snapshot (commit hash, manifest, configs, environment files) for each experiment.

## Timeline & Milestones
- To be announced (TBA)
