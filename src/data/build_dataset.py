import json
from pathlib import Path

import pandas as pd

from src.utils.config import load_config


def build_dataset():
    data_cfg = load_config("data")
    input_file = Path(data_cfg["interim_dir"]) / "features.json"
    output_file = Path(data_cfg["processed_dir"]) / data_cfg["dataset_filename"]
    Path(data_cfg["processed_dir"]).mkdir(parents=True, exist_ok=True)

    with open(input_file) as f:
        features = json.load(f)

    df = pd.DataFrame(features)
    df.to_csv(output_file, index=False)
    print(f"[build_dataset] Mock dataset saved to {output_file}")
    return output_file


def main():
    build_dataset()


if __name__ == "__main__":
    main()
