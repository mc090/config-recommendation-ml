# Effectiveness Analysis of Selected Machine Learning Models in Recommending Configuration Files Based on the Structure of Software Projects

> 🚧 Work in Progress

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

## Project Structure (key folders)
```
.devcontainer/        # DevContainer + Dockerfile
data/                 # raw, interim, processed dataset snapshots
docs/                 # dataset_card, experiment_plan, model_card, reproducibility checklist
notebooks/            # EDA and experiment notebooks
src/                  # pipeline scripts (pipeline_init, config, logger, utils, github_client)
src/data/             # data pipeline stages (fetch_raw, extract_structure, enrich_content, compute_features, build_dataset)
environment/          # Conda environment YAMLs
```

## Reproducibility snapshot (how to reference an experiment)
- Git commit: `git rev-parse HEAD`
- Dataset manifest: `data/processed/vX.Y.Z/manifest.json` (each processed snapshot MUST include a manifest)
- Environment: `environment/environment-base.yaml` ([here](./environment/environment-base.yaml)) and `environment/environment-torch.yaml` ([here](./environment/environment-torch.yaml))
- Settings: the values from `.env` / `src/config.py` used for the run (captured automatically in `logs/config_<run_id>.json` by `pipeline_init`)

Example reproducibility citation you should save with experiments:
```
commit: <git-hash>
dataset_manifest: data/processed/v1.2.0/manifest.json
config_snapshot: logs/config_<run_id>.json
environment:
	- environment/environment-base.yaml
	- environment/environment-torch.yaml
```

## Documentation & Links
- [Dataset card](./docs/dataset_card.md) — schema, collection process, manifest template, and ethical considerations.
- [Experiment plan](./docs/experiment_plan.md) — experiments, baselines, cross-validation strategy, and timelines.
- [Model card](./docs/model_card.md) — model details, intended use, limitations, and deployment notes.
- [Reproducibility checklist](./docs/reproducibility_checklist.md) — step-by-step reproduction items linked to scripts.

## Dataset
For full dataset schema, collection details, and versioning policy, see [Dataset card](./docs/dataset_card.md).

## License & Contact
Distributed under the MIT License. See [License](./LICENSE).
For questions or collaboration, open an issue or contact the repository owner via the GitHub profile.
