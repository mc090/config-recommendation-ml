import json

import pandas as pd

from config_recommendation_ml.utils.config import load_config
from config_recommendation_ml.utils.paths import INTERIM_DATA_DIR, PROCESSED_DATA_DIR


def build_dataset():
    data_cfg = load_config("data")
    input_file = INTERIM_DATA_DIR / "features.json"
    output_file = PROCESSED_DATA_DIR / data_cfg["dataset_filename"]

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
