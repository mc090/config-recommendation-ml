import json
import random

from config_recommendation_ml.utils.config import load_config
from config_recommendation_ml.utils.paths import RAW_DATA_DIR


def fetch_raw():
    seeds_cfg = load_config("seeds")
    github_cfg = load_config("github")

    random.seed(seeds_cfg["data_seed"])

    repo_metadata = github_cfg["sample_repos"]
    output_file = RAW_DATA_DIR / "raw_metadata.json"
    with open(output_file, "w") as f:
        json.dump(repo_metadata, f)
    print(f"[fetch_raw] Saved mock raw metadata to {output_file}")
    return output_file


def main():
    fetch_raw()


if __name__ == "__main__":
    main()
