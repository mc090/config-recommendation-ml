from pathlib import Path

import yaml


def load_config(name: str):
    """
    Load YAML config from config/{name}.yaml
    """
    path = Path("config") / f"{name}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)
