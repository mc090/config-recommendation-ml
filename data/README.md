# GitHub Python Repository Structure Dataset

## Overview
This dataset contains information about the structure of Python projects collected from public GitHub repositories. It is intended to help develop ML models that recommend configuration files (e.g., `Dockerfile`, `pyproject.toml`, `.pre-commit-config.yaml`) based on repository structure.

The base snapshot is intentionally redundant; later preprocessing (feature engineering, attribute selection) will refine the dataset.

## Data Sources
- GitHub public repositories retrieved using the GitHub API.
- Repository selection criteria: TBA

⚠️ **Disclaimer**: This dataset contains file-structure metadata only and does not redistribute source code content.

## Dataset schema
See the full schema and field explanations in the [Dataset Card](../docs/dataset_card.md).

## Versioning and Manifest
Processed dataset snapshots are saved in `data/processed/vX.Y.Z/`.
Each snapshot MUST include a `manifest.json` containing at minimum: `version`, `created_at` (ISO8601), `script`, `git_commit`, `preprocessing`, `rows`, `checksum`.

Refer to [Dataset Card](../docs/dataset_card.md) for the manifest template and versioning policy.

## Example Row
```json
{
  "repo_url": "https://github.com/user/repo",
  "stars": 1234,
  "forks": 56,
  "created_at": "2020-01-01T00:00:00Z",
  "last_updated": "2025-11-01T12:00:00Z",
  "num_files": 42,
  "num_py_files": 12,
  "num_js_files": 2,
  "num_test_files": 5,
  "has_dockerfile": false,
  "has_pyproject_toml": true,
  "top_level_dirs": ["src", "tests", "docs"]
}
```

## License
See `LICENSE` for terms of use. This dataset is distributed under the same license as the repository.

## Files Structure
- `raw/` — Unprocessed, downloaded data
- `interim/` — Intermediate files
- `processed/` — Final dataset snapshots (with manifest)

See the [main project README](../README.md) for more details.

## Related Documentation
- [Dataset card](../docs/dataset_card.md)
