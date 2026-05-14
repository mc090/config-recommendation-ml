# Model Card

## Intended Use
This model is intended solely for research, focusing on recommending configuration files for Python programming projects. It supports studies in automated configuration and software analytics. The scope is intentionally restricted to Python repositories to ensure label coherence and feature relevance.

## Model Architecture
Current training compares machine learning models from different families:
- Decision Tree
- Random Forest
- Gradient Boosting
- SVM
- Neural Network (PyTorch-backed estimator)

Training is executed as settings-driven `GridSearchCV` per `(variant, model_family)` run.

## Training Data and Preprocessing
Training data is sourced from the Public GitHub Repositories Structure Metadata dataset ([Dataset card](./dataset_card.md)), restricted to Python repositories only. The dataset collects a broad set of configuration file presence labels. Current ML experiments use a single multiclass target created from three primary labels: `has_pyproject_toml`, `has_dockerfile`, and `has_github_actions` (classes `000`..`111`).

### Implemented workflow
1. Generate feature-pruned dataset variants: `python -m src.experiments.build_variants`
2. Train selected model families on chosen variants: `python -m src.experiments.training.run_training`
3. Evaluate using 10-fold `StratifiedKFold` on the multiclass label-combination target (`000`..`111`).

## Model Version and Training Dates
- **Versioning**: Training results are versioned by `run_id` under `logs/training/<run_id>/`.
- **Training Date**: Stored per run in `run_config.json` (`created_at`) and MLflow metadata.

## Evaluation Metrics
Each model is evaluated using cross-validation metrics tracked in training:
- Accuracy
- Balanced accuracy
- Precision (macro, micro, weighted)
- Recall (macro, micro, weighted)
- F1-score (macro, micro, weighted)

## Artifacts and Reproducibility
Run-level performance summaries are persisted in:
- `logs/training/<run_id>/cv_summary.csv`
- `logs/training/<run_id>/cv_candidates.csv`
- `logs/training/<run_id>/hyperparameter_impact.csv`
- `logs/training/<run_id>/timing_summary.csv`
- `notebooks/06_training_results_analysis.ipynb` exports under `notebooks/artifacts/training_results/<run_id>_v<dataset_version>/`

For reproducibility, also archive:
- `logs/training/<run_id>/run_config.json`
- MLflow run metadata/artifacts for each variant-model pair.
- The full procedure in [Reproducibility checklist](./reproducibility_checklist.md).

## Known Limitations and Biases
Based on `notebooks/06_training_results_analysis.ipynb` outputs (run `20260413_155156`, dataset `v1.0.1`):
- **Class-imbalance sensitivity**: rare label combinations are learned poorly. In per-class analysis for the selected best setup (`manual_selection` + `gradient_boosting`), class `110` (2.46% support) had `F1=0.0`, while majority classes (`101`, `111`, `000`) reached much higher scores.
- **Confusion between semantically close classes**: high confusion was observed for minority combinations (e.g., `011 -> 111`, `001 -> 101`, `010 -> 000`), indicating limited separability for less frequent patterns.
- **Global performance ceiling**: best weighted F1 is moderate (around `0.48`), and balanced accuracy remains relatively low (around `0.32`), which indicates uneven performance across classes despite acceptable overall accuracy.
- **Compute-performance trade-off**: gradient boosting delivered the best overall quality but required substantially longer training time than tree/SVM baselines, so conclusions may be sensitive to compute budget constraints.
- **Feature-pruning bias risk**: variant strategies improve efficiency/robustness differently, but manual feature removal introduces expert-selection bias, and aggressive pruning can drop informative correlated or rare-signal features.
