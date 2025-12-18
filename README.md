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

3) Run a minimal data pipeline (example)
```bash
# fetch raw metadata from GitHub according to config
python src/data/fetch_raw.py --config config/data.yaml
# build processed dataset snapshot
python src/data/build_dataset.py --config config/data.yaml
# compute features used by experiments
python src/data/compute_features.py --config config/features.yaml
```

4) Quick exploration
```bash
# open notebook for exploration
code notebooks/01_explore_dataset.ipynb
# or print manifest (example path)
python -c "import json; print(json.load(open('data/processed/latest/manifest.json')))"
```

## Common Workflows (one-liners)
- Collect raw metadata: `python src/data/fetch_raw.py --config config/data.yaml`
- Build processed snapshot: `python src/data/build_dataset.py --config config/data.yaml`
- Compute features: `python src/data/compute_features.py --config config/features.yaml`
- Explore dataset: open `notebooks/01_explore_dataset.ipynb` ([here](./notebooks/01_explore_dataset.ipynb))
- Run experiments: see [Experiment plan](docs/experiment_plan.md) for mapping to notebooks/scripts and [Training config](config/training.yaml) for parameters

## Project Structure (key folders)
```
.devcontainer/        # DevContainer + Dockerfile
data/                 # raw, interim, processed dataset snapshots
docs/                 # dataset_card, experiment_plan, model_card, reproducibility checklist
notebooks/            # EDA and experiment notebooks
src/                  # data collection and preprocessing scripts
config/               # YAML configs for data, features, training, evaluation
environment/          # Conda environment YAMLs
```

## Reproducibility snapshot (how to reference an experiment)
- Git commit: `git rev-parse HEAD`
- Dataset manifest: `data/processed/vX.Y.Z/manifest.json` (each processed snapshot MUST include a manifest)
- Environment: `environment/environment-base.yaml` ([here](./environment/environment-base.yaml)) and `environment/environment-torch.yaml` ([here](./environment/environment-torch.yaml))
- Configs: the exact YAML files used from `config/` (include path and any overrides)

Example reproducibility citation you should save with experiments:
```
commit: <git-hash>
dataset_manifest: data/processed/v1.2.0/manifest.json
configs:
	- config/data.yaml
	- config/features.yaml
	- config/training.yaml
environment:
	- environment/environment-base.yaml
	- environment/environment-torch.yaml
```

## Documentation & Links
- [Dataset card](./docs/dataset_card.md) — schema, collection process, manifest template, and ethical considerations.
- [Experiment plan](./docs/experiment_plan.md) — experiments, baselines, cross-validation strategy, and timelines.
- [Model card](./docs/model_card.md) — model details, intended use, limitations, and deployment notes.
- [Reproducibility checklist](./docs/reproducibility_checklist.md) — step-by-step reproduction items linked to scripts.
- [Changelog](./CHANGELOG.md)
- [Roadmap](./ROADMAP.md)
- [Contributing](./CONTRIBUTING.md)

## Dataset
For full dataset schema, collection details, and versioning policy, see [data README](./data/README.md) and [Dataset card](./docs/dataset_card.md).

## Roadmap
See [Roadmap](./ROADMAP.md) for planned features, experiments, and milestones. Major releases and dataset snapshots will be tagged and documented.

## Changelog
See [Changelog](./CHANGELOG.md) for a history of notable changes and releases.

## Citation
If you re-use or cite this project in your thesis or a paper, use a citation similar to:
```bibtex
@misc{config-recommendation-ml,
	author = {Your Name},
	title = {Effectiveness Analysis of Selected ML Models for Recommending Configuration Files},
	year = {2025},
	howpublished = {GitHub repository},
	url = {https://github.com/mc090/config-recommendation-ml}
}
```

## Contributing
See [Contributing](./CONTRIBUTING.md) for guidelines on environment setup, testing, and submitting issues or pull requests. Preferred workflow: fork → branch → pull request. Include updated `manifest.json` and `config` changes for data-related PRs. Before major structural changes, open an issue to discuss. Incremental, non-breaking improvements are preferred.

## License & Contact
Distributed under the MIT License. See [License](./LICENSE).
For questions or collaboration, open an issue or contact the repository owner via the GitHub profile.
