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
   - Run the full pipeline (recommended):
     ```bash
     dvc repro
     ```
   - Or run individual stages manually (debugging only):
     ```bash
     python -m src.pipeline_init
     python -m src.data.fetch_raw
     python -m src.data.extract_structure
     python -m src.data.enrich_content
     python -m src.data.compute_features
     python -m src.data.build_dataset
     ```
   - Pipeline configuration is driven by `.env` (see `src/config.py`). A config snapshot is saved automatically to `logs/config_<run_id>.json` by `pipeline_init`.
   - Generate experiment variants from the latest dataset:
     ```bash
     python -m src.experiments.build_variants
     ```
   - Variant artifacts are saved under `data/processed/vX.Y.Z/variants/`:
     - per-variant `dataset.csv` and `variant_manifest.json`
     - root-level `variants_manifest.json` and `variant_overview.csv`
4. **Explore dataset and variants**
    - Open and run exploratory notebooks:
      - [01_test_dataset_building.ipynb](../notebooks/01_test_dataset_building.ipynb)
      - [02_correlation_analysis.ipynb](../notebooks/02_correlation_analysis.ipynb)
      - [03_dataset_insights.ipynb](../notebooks/03_dataset_insights.ipynb)
      - [04_variant_generation.ipynb](../notebooks/04_variant_generation.ipynb)
      - [05_variant_statistics.ipynb](../notebooks/05_variant_statistics.ipynb)
    - Artifact outputs:
      - Exploratory artifacts (correlation/distributions/labels) are written to `notebooks/artifacts/`.
      - These exploratory outputs are latest-snapshot files and may be overwritten by later runs.
5. **Run experiments**
    - Use scripts and config files as described in [Experiment plan](experiment_plan.md)
    - Run training pipeline:
      ```bash
      python -m src.experiments.training.run_training
      ```
    - Training run outputs are saved under `logs/training/<run_id>/` and tracked in MLflow (`cv_summary.csv`, `cv_candidates.csv`, `hyperparameter_impact.csv`, `run_config.json`, `timing_summary.csv`).
    - Open MLflow UI (matching current default file-based tracking):
      ```bash
      mlflow ui --backend-store-uri file:./logs/mlruns --host 0.0.0.0 --port 5000
      ```
6. **Analyze training outputs**
    - Open and run result-analysis notebooks:
      - [06_training_results_analysis.ipynb](../notebooks/06_training_results_analysis.ipynb)
      - [07_shap_analysis.ipynb](../notebooks/07_shap_analysis.ipynb)
    - Dependencies:
      - `06_training_results_analysis.ipynb` requires training artifacts (for example `cv_summary.csv`) from `logs/training/<run_id>/`.
      - `07_shap_analysis.ipynb` reuses best params from training outputs and computes class-aggregate SHAP values.
    - Notebook artifact policy:
      - Training/SHAP analysis artifacts are versioned in both folder and filename:
        - `notebooks/artifacts/training_results/<run_id>_v<dataset_version>/...`
        - `notebooks/artifacts/shap/<run_id>_v<dataset_version>/...`
