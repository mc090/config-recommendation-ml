import json
import random
from pathlib import Path

from src.utils.config import load_config


def compute_features():
    data_cfg = load_config("data")
    features_cfg = load_config("features")
    seeds_cfg = load_config("seeds")
    random.seed(seeds_cfg["sampling_seed"])

    input_file = Path(data_cfg["interim_dir"]) / "structure.json"
    output_dir = Path(data_cfg["interim_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

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
