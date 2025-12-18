import json
import random

from config_recommendation_ml.utils.config import load_config
from config_recommendation_ml.utils.paths import INTERIM_DATA_DIR, RAW_DATA_DIR


def extract_structure():
    seeds_cfg = load_config("seeds")
    random.seed(seeds_cfg["sampling_seed"])

    input_file = RAW_DATA_DIR / "raw_metadata.json"
    output_dir = INTERIM_DATA_DIR

    with open(input_file) as f:
        raw_metadata = json.load(f)

    extracted = []
    for repo in raw_metadata:
        extracted.append(
            {
                "repo_url": repo["repo_url"],
                "num_py_files": random.randint(1, 10),
                "num_js_files": random.randint(0, 5),
                "num_notebooks": random.randint(0, 3),
            }
        )

    output_file = output_dir / "structure.json"
    with open(output_file, "w") as f:
        json.dump(extracted, f)
    print(f"[extract_structure] Saved mock structure to {output_file}")
    return output_file


def main():
    extract_structure()


if __name__ == "__main__":
    main()
