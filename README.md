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

## 📄 License
Distributed under the MIT License. See LICENSE for details.
