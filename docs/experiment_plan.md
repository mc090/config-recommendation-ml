# Experiment Plan

## Overview
The main goal of these experiments is to develop the most effective machine learning model for recommending configuration files for programming projects. Various ML models will be compared, and different preprocessing methods may also be explored.

## Variants

Before split/CV and model training, generate feature-pruned dataset variants with a CLI-first workflow:

- Run:
  ```bash
  python -m src.experiments.build_variants
  ```
- Variants are saved under the latest dataset version:
  - `variants/original`
  - `variants/corr_<threshold>` (for each given threshold e.g. `corr_060` for `0.60`)
  - `variants/manual_selection`
  - `variants/dom_<threshold>` (e.g. `dom_080` for `0.80`)
- Output artifacts:
  - per-variant `dataset.csv` and `variant_manifest.json`
  - root-level `variants_manifest.json` and `variant_overview.csv`
- Preprocessing rules (configuration-driven via `src/config.py`):
  - Correlation thresholds: `variant_correlation_thresholds` (current defaults: `0.70`, `0.60`)
  - Correlation significance: `variant_correlation_pvalue_threshold` (current default: `0.05`)
  - Dominance threshold: `variant_dominance_threshold` (current default: `0.80`)
  - Manual removals: `variant_selected_features_for_pruning`
- Correlation pruning skips invalid pairs (`<2` valid samples or constant input); each skipped pair is logged.
- Notebook support for reproducibility/statistics:
  - `notebooks/04_variant_generation.ipynb`
  - `notebooks/05_variant_statistics.ipynb`

## Dataset Splitting Strategy

The dataset CSV contains unsplit data. Training uses full-dataset cross-validation (no pre-training spliting).

### Recommended Approach:

1. **10-fold stratified CV on full dataset** using a multiclass target built from:
   - `has_pyproject_toml`
   - `has_dockerfile`
   - `has_github_actions`
   
   Example classes: `110`, `000`, `101` (up to 8 total combinations).

2. **Fail-fast rarity rule**: if any combination count is lower than CV folds, fail with a clear error and adjust dataset/filtering before training.

3. **Model ranking**: compare candidates by the configured refit metric (`training_gridsearch_refit_metric`) from CV folds.

## Metrics
- Accuracy (standard and balanced)
- Precision, Recall, F1-score (macro, micro and weighted)
- Report mean ± std across CV folds

## Hyperparameter Tuning Plan
- GridSearchCV only (settings-driven parameter spaces from `.env` / `src/config.py`).
- Locked model families:
  - Decision Trees
  - Random Forest
  - Gradient Boosting
  - SVM
  - Neural Networks (PyTorch backend)

## Seeds
Random seeds (`random_seed`) are configured via `.env` and read by `src/config.py`. The active seed value is captured automatically in `logs/config_<run_id>.json` for every pipeline run.

## Compute Budget
Experiments were runned on local machine with NVIDIA RTX 2060 GPU.
