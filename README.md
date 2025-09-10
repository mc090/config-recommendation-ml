# Effectiveness Analysis of Selected Machine Learning Models in Recommending Configuration Files Based on the Structure of Software Projects

> 🚧 Work in Progress

## 📖 About
This project is the practical part of my Master's thesis for the Computer Science program at the University of Silesia in Katowice.

My goal is to explore **machine learning from scratch** by:
- Creating and managing **my own dataset**.
- Training and comparing different ML models.
- Experimenting with preprocessing and evaluation techniques.

Everything runs inside a reproducible **Dev Container** with **Conda** for dependency management.

## Project Structure
```bash
.
├── .devcontainer/              # Devcontainer setup with Dockerfile
├── data/                       # Custom dataset
├── notebooks/                  # Jupyter notebooks for exploration
├── src/                        # Application logic
├── .pre-commit-config.yaml     # Pre-commit confguration file
├── environment-base.yaml       # Conda environment definition with basic packages
├── environment-torch.yaml      # Conda environment definition with torch related packages
├── pyproject.toml              # Project metadata and ruff configuration
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- [Docker](https://www.docker.com/)
- [VS Code](https://code.visualstudio.com/) with [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- [Conda](https://anaconda.org/anaconda/conda) (for local development outside of container)


### Installation
```bash
# Clone the repository
git clone https://github.com/mc090/config-recommendation-ml.git
cd config-recommendation-ml
```

### Opening in Devcontainer
Open the repo in VS Code.
When prompted, "Reopen in Container".
The devcontainer will automatically install Conda and create the project environment from environment.yml.

### Install locally
To install locally you need to have conda installed.
```bash
# Create virtual environment
conda env create --name config-recommendation-ml --file environment-base.yaml --file environment-torch.yaml

# Activate virtual environment
conda activate config-recommendation-ml
```

## 📍 Project Roadmap

### Phase 1: Setup & Foundation

#### 1.1 Repo & Environment

* 🟩 Initialize Git repository
* 🟩 Configure Dev Container (Dockerfile + devcontainer.json)
* 🟩 Add Conda environment (`environment.yml`)

#### 1.2 Code Quality & Standards

* 🟩 Set up pre-commit with ruff (linting, formatting)
* 🟩 Decide project folder structure

---

### Phase 2: Dataset Creation & Management

#### 2.1 Dataset schema

* ◻️ Define attributes of dataset

#### 2.1 Data Acquisition

* ◻️ Find way to optain data
* ◻️ Define dataset source(s)

#### 2.2 Preprocessing Pipeline

* ◻️ Implement dataset loader
* ◻️ Add preprocessing functions (cleaning, normalization, encoding)
* ◻️ Split into train/val/test
* ◻️ Save processed dataset (`data/processed/`)

#### 2.3 Versioning

* ◻️ Decide dataset versioning method (start simple: Git, later MLflow/DVC)
* ◻️ Store preprocessing parameters alongside dataset version

---

### Phase 3: Baseline Models

#### 3.1 Model Training

* ◻️ Train baseline model (Logistic Regression)
* ◻️ Store training script in `src/models/baseline.py`

#### 3.2 Evaluation

* ◻️ Define metrics (accuracy, F1, confusion matrix)
* ◻️ Implement evaluation script

#### 3.3 Logging

* ◻️ Log parameters, metrics, and artifacts in MLflow
* ◻️ Verify reproducibility (same results on re-run)

---

### Phase 4: Model Comparison & Experimentation

#### 4.1 Try Different Models

* ◻️ Decision Tree
* ◻️ Random Forest
* ◻️ Support Vector Machine
* ◻️ k-Nearest Neighbors

#### 4.2 Hyperparameter Tuning

* ◻️ Implement simple search (grid/random)
* ◻️ Log all runs in MLflow
* ◻️ Compare metrics visually

#### 4.3 Preprocessing Experiments

* ◻️ With/without scaling
* ◻️ Feature selection
* ◻️ Dimensionality reduction (PCA, etc.)

---

### Phase 5: Reproducibility & Documentation

#### 5.1 Reproducibility

* ◻️ Ensure MLflow logs Conda environment (`mlflow conda.yaml`)
* ◻️ Add `Makefile` or task runner (common commands: `make train`, `make eval`)
* ◻️ Document reproducibility steps in README

#### 5.2 Documentation

* ◻️ Update README with roadmap, setup, and usage
* ◻️ Write docstrings & comments
* ◻️ Create example notebook demonstrating workflow

#### 5.3 Results & Reflection

* ◻️ Summarize best models + findings
* ◻️ Write lessons learned (what worked, what didn’t)
* ◻️ Define possible next directions (e.g., deployment, deeper ML topics)

## 📄 License
Distributed under the MIT License. See LICENSE for details.
