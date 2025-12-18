# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
- Project initialization
- Added documentation skeletons
- Dataset schema and manifest template
- Preprocessing pipeline and end-to-end data workflow

### Added
- `src/data/fetch_raw.py`: mock raw data fetcher
- `src/data/extract_structure.py`: structure extraction (interim/structure.json)
- `src/data/compute_features.py`: feature computation (interim/features.json)
- `src/data/build_dataset.py`: builds processed dataset from features (data/processed/dataset.csv)
- `dvc.yaml`: DVC stages for fetch, extract, compute, and build
- `config/*.yaml`: added `data.yaml`, `features.yaml`, `training.yaml`, `evaluation.yaml`, `model.yaml`, `github.yaml`, `seeds.yaml`
- `environment/`: Conda environment files `environment-base.yaml` and `environment-torch.yaml`
- `.devcontainer/Dockerfile` updated to use `environment/environment-base.yaml`
- `notebooks/01_explore_dataset.ipynb`: end-to-end pipeline notebook (fetch → extract → compute → build)
- Documentation: `docs/dataset_card.md`, `docs/experiment_plan.md`, `docs/model_card.md`, `docs/reproducibility_checklist.md`, `docs/README.md`
- `CONTRIBUTING.md`, `ROADMAP.md`

### Changed
- `README.md`: updated Quick Start, workflows, and reproducibility instructions
- `data/README.md`: updated dataset notes and manifest guidance

### Data artifacts (added under `data/`)
- `data/raw/raw_metadata.json` (mock)
- `data/interim/structure.json` (mock)
- `data/interim/features.json` (mock)
- `data/processed/dataset.csv` (mock snapshot)

Notes: these changes add a runnable mock pipeline and initial dataset snapshots suitable for development and testing. Update entries as real data and commit hashes become available.

## [0.1.0] - 2025-11-18
- Initial release: setup, environment files, basic documentation
