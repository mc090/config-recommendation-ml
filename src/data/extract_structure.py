import json
import random
from pathlib import Path

from src.utils.config import load_config


def extract_structure():
    data_cfg = load_config("data")
    seeds_cfg = load_config("seeds")
    random.seed(seeds_cfg["sampling_seed"])

    input_file = Path(data_cfg["raw_dir"]) / "raw_metadata.json"
    output_dir = Path(data_cfg["interim_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

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
