# Reproducibility Checklist

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
