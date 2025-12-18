import json
import random

from config_recommendation_ml.utils.config import load_config
from config_recommendation_ml.utils.paths import INTERIM_DATA_DIR


def compute_features():
    features_cfg = load_config("features")
    seeds_cfg = load_config("seeds")
    random.seed(seeds_cfg["sampling_seed"])

    input_file = INTERIM_DATA_DIR / "structure.json"
    output_dir = INTERIM_DATA_DIR

    with open(input_file) as f:
        structure = json.load(f)

    features = []
    for repo in structure:
        feat = repo.copy()
        if features_cfg.get("compute_avg_files_per_dir", True):
            feat["avg_files_per_dir"] = random.randint(1, 5)
        features.append(feat)

    output_file = output_dir / "features.json"
    with open(output_file, "w") as f:
        json.dump(features, f)
    print(f"[compute_features] Saved mock features to {output_file}")
    return output_file


def main():
    compute_features()


if __name__ == "__main__":
    main()
