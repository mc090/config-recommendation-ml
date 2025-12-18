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

## Mapping to Scripts/Notebooks
- [Data preparation](src/data/build_dataset.py)
- [Feature computation](src/data/compute_features.py)
- [Exploration](notebooks/01_explore_dataset.ipynb)
- Model training/evaluation (TBA)

## Reproducibility Steps
1. Clone the repository and set up the environment as described in the [README](../README.md).
2. Prepare the dataset using provided scripts and configuration files.
3. Run experiments using the specified scripts/notebooks and configuration YAMLs.
4. Save and reference the reproducibility snapshot (commit hash, manifest, configs, environment files) for each experiment.

## Timeline & Milestones
- To be announced (TBA)
