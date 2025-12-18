# Reproducibility Checklist

This checklist tracks all practices and tools used to ensure experiments and results in this project can be reliably repeated.

## Data
- [x] Dataset schema documented ([Dataset card](dataset_card.md))
- [x] Manifest template provided ([Dataset card](dataset_card.md))
- [ ] Data versioning (planned: DVC or MLflow integration)

## Environment
- [x] Conda environment files included ([environment-base.yaml](../environment/environment-base.yaml), [environment-torch.yaml](../environment/environment-torch.yaml))
- [x] Devcontainer setup for reproducible development ([.devcontainer/](../.devcontainer/))
- [ ] Dockerfile for full environment capture (planned)

## Code & Experiments
- [x] Source code tracked in Git, tagged releases
- [ ] Training/evaluation scripts with config files (in progress; see [build_dataset.py](../src/data/build_dataset.py), [compute_features.py](../src/data/compute_features.py))
- [ ] Random seed control in all scripts (planned)
- [ ] MLflow logging for experiments (planned)

## Results
- [ ] Scripts/notebooks to reproduce key figures and metrics (planned; see [01_explore_dataset.ipynb](../notebooks/01_explore_dataset.ipynb))

## Documentation
- [x] README, dataset card, model card, experiment plan

---

## Step-by-Step Reproduction Guide

1. **Clone the repository**
   ```bash
   git clone https://github.com/mc090/config-recommendation-ml.git
   cd config-recommendation-ml
   ```
2. **Set up the environment**
   - Use VS Code Dev Container (recommended)
   - Or create Conda environment:
     ```bash
     conda env create --name config-recommendation-ml --file environment/environment-base.yaml --file environment/environment-torch.yaml
     conda activate config-recommendation-ml
     ```
3. **Prepare the dataset**
   - Fetch raw data:
     ```bash
     python src/data/fetch_raw.py --config config/data.yaml
     ```
   - Build processed dataset:
     ```bash
     python src/data/build_dataset.py --config config/data.yaml
     ```
   - Compute features:
     ```bash
     python src/data/compute_features.py --config config/features.yaml
     ```
4. **Explore and analyze**
   - Open and run notebooks:
     - [01_explore_dataset.ipynb](../notebooks/01_explore_dataset.ipynb)
5. **Run experiments**
   - Use scripts and config files as described in [Experiment plan](experiment_plan.md)
6. **Track reproducibility**
   - Save reproducibility snapshot: commit hash, manifest, configs, environment files
   - Include `config/seeds.yaml` (or record the random seeds used) with the reproducibility snapshot
   - Reference [README](../README.md) for reproducibility citation format
