import json
import random
from pathlib import Path

from src.utils.config import load_config


def fetch_raw():
    data_cfg = load_config("data")
    seeds_cfg = load_config("seeds")

    random.seed(seeds_cfg["data_seed"])

    raw_dir = Path(data_cfg["raw_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)

    repo_metadata = [
        {"repo_url": "https://github.com/user/repo1", "stars": random.randint(0, 50)},
        {"repo_url": "https://github.com/user/repo2", "stars": random.randint(0, 50)},
    ]
    output_file = raw_dir / "raw_metadata.json"
    with open(output_file, "w") as f:
        json.dump(repo_metadata, f)
    print(f"[fetch_raw] Saved mock raw metadata to {output_file}")
    return output_file


def main():
    fetch_raw()


if __name__ == "__main__":
    main()
