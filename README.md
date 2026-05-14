# Effectiveness Analysis of Selected Machine Learning Models in Recommending Configuration Files Based on the Structure of Software Projects

## 📖 About
This project serves as the practical component of my Master's thesis in the Computer Science program at the University of Silesia in Katowice.

The primary aim is to delve into **machine learning from the ground up** by:
- Developing and managing **a custom dataset**.
- Training and evaluating various ML models.
- Experimenting with preprocessing techniques and evaluation methods.

The entire workflow operates within a reproducible **Dev Container** environment, utilizing **Conda** for dependency management.

## Quick Start
These commands assume a local bash shell or opening the repository in the VS Code Dev Container.

1) Open in VS Code Dev Container
- Use the VS Code command palette: `Remote-Containers: Reopen in Container` (Dev Container will install Conda and set up the environment).

2) Local setup
```bash
conda env create --name config-recommendation-ml --file environment/environment-base.yaml --file environment/environment-torch.yaml
conda activate config-recommendation-ml
```

3) Build the dataset snapshot
```bash
dvc repro
```

4) Generate dataset variants (experiment preparation)
```bash
python -m src.experiments.build_variants
```
This creates `original`, `corr_<threshold>` (for every given threshold), `manual_selection`, and
`dom_<threshold>` under `data/processed/vX.Y.Z/variants/`. Thresholds are passed throught `.env` file, additionaly:
- per-variant `dataset.csv` and `variant_manifest.json`
- root-level `variants_manifest.json` and `variant_overview.csv`

5) Train models
```bash
python -m src.experiments.training.run_training
```
Training configuration (model families, GridSearch ranges, CV folds, tracking) is
loaded from `.env` via `src/config.py`.


## Project Structure (key folders)
```
.devcontainer/              # DevContainer + Dockerfile
data/                       # raw, interim, processed dataset snapshots
docs/                       # dataset_card, experiment_plan, model_card, reproducibility checklist
environment/                # Conda environment YAMLs
notebooks/                  # EDA and experiment notebooks
src/                        # source code of the project
src/data/                   # data pipeline stages
src/experiments/training    # training pipeline
```

## Reproducibility snapshot (how to reference an experiment)
- Git commit: `git rev-parse HEAD`
- Dataset manifest: `data/processed/vX.Y.Z/manifest.json` (each processed snapshot MUST include a manifest)
- Environment: `environment/environment-base.yaml` and `environment/environment-torch.yaml`
- Settings: the values from `.env` / `src/config.py` used for the run (captured automatically in `logs/config_<run_id>.json` by `pipeline_init`)

## Documentation
- [Dataset card](./docs/dataset_card.md) — schema, collection process, manifest template, and versioning policy.
- [Experiment plan](./docs/experiment_plan.md) — experiments, baselines and cross-validation strategy.
- [Model card](./docs/model_card.md) — model details, intended use and limitations.
- [Reproducibility checklist](./docs/reproducibility_checklist.md) — step-by-step reproduction items linked to scripts.

## Dataset
For full dataset schema, collection details, and versioning policy, see [Dataset card](./docs/dataset_card.md).

## License & Contact
Distributed under the MIT License. See [License](./LICENSE).
For questions or collaboration, open an issue or contact the repository owner via the GitHub profile.
