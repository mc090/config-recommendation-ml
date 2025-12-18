import yaml

from config_recommendation_ml.utils.paths import CONFIG_DIR


def load_config(name: str):
    """
    Load YAML config from config/{name}.yaml
    """
    path = CONFIG_DIR / f"{name}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)
