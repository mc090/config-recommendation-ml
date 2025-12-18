# Dataset Card

## Name and Version
- **Name**: Public GitHub Repositories Structure Metadata
- **Version**: 1.0.0

## Motivation
My motivation for creating this dataset is to explore the process of building a custom dataset and to have a dedicated resource for further processing in machine learning models. This work forms the foundation of my thesis.

## Intended Use
The primary intended use is to train machine learning models for configuration recommendation systems. The dataset is also suitable for research in software analytics and automated tooling.

## Data Sources and Selection Criteria
- **Sources**: GitHub repositories collected via the GitHub API.
- **Selection Criteria**: TBA

## Schema
TBA

### Attributes
| Name | Type | Description | Example |
|---|---|---|---|
| `repo_url` | string | Link to the GitHub repository | `https://github.com/user/repo` |
| `stars` | int | Number of stars in GitHub repository | `1234` |
| `forks` | int | Number of forks in GitHub repository | `56` |
| `created_at` | string (ISO8601) | Date of creation (format: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`) | `2020-01-01T00:00:00Z` |
| `last_updated` | string (ISO8601) | Date of last update (format: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`) | `2025-11-01T12:00:00Z` |
| `num_files` | int | Total number of files | `42` |
| `num_py_files` | int | Number of Python files | `12` |
| `num_js_files` | int | Number of JavaScript files | `2` |
| `num_ts_files` | int | Number of TypeScript files | `0` |
| `num_html_files` | int | Number of HTML files | `1` |
| `num_css_files` | int | Number of CSS files | `0` |
| `num_json_files` | int | Number of JSON files | `3` |
| `num_sh_files` | int | Number of Shell files | `1` |
| `num_test_files` | int | Number of test files | `5` |
| `num_docs_files` | int | Number of documentation files (.md or .rst) | `2` |
| `num_notebooks` | int | Number of Jupyter Notebook files | `0` |
| `other_extensions_count` | int | Number of files with other extensions | `4` |
| `has_tests_dir` | bool | Presence of `/tests` directory | `true` |
| `num_dirs` | int | Total number of directories | `8` |
| `top_level_dirs` | [string] | List of top-level directories | `['src','tests','docs']` |
| `avg_files_per_dir` | float | Average number of files per directory | `5.25` |
| `avg_py_file_len` | int | Average length of Python file (lines) | `200` |
| `avg_nb_file_len` | int | Average length/size of notebook files | `150` |
| `avg_docs_file_len` | int | Average length of documentation files | `120` |
| `num_dependencies` | int | Number of declared dependencies | `10` |
| `repo_age_days` | int | Days since repository creation | `1500` |
| `recent_activity_days` | int | Days since last change in repository | `20` |

### Labels
| Name | Type | Description | Example |
|---|---|---|---|
| `has_requirements_txt` | bool | Presence of `requirements.txt` | `false` |
| `has_conda_env` | bool | Presence of `environment*.yaml` | `true` |
| `has_pyproject_toml` | bool | Presence of `pyproject.toml` | `false` |
| `has_pyproject_lock` | bool | Presence of `pyproject.lock` | `false` |
| `has_github_actions` | bool | Presence of `.github/workflows/` | `true` |
| `has_dockerfile` | bool | Presence of `Dockerfile` | `false` |
| `has_docker_compose` | bool | Presence of `docker-compose.yaml` | `false` |
| `has_precommit_config` | bool | Presence of `.pre-commit-config.yaml` | `true` |

## Collection and Preprocessing Steps
- **Collection**: TBA
- **Preprocessing**: TBA

## Limitations and Ethical Considerations
- **Limitations**: The dataset may not represent all types of software projects, as it focuses on repositories with specific characteristics that meets intended selection criteria.
- **Ethical Considerations**: Ensure proper attribution to repository authors. Avoid using the dataset for malicious purposes, such as generating harmful configurations.

## Recommended Splits and Versioning Policy
- **Splits**: Train (70%), Validation (15%), Test (15%).
- **Versioning**: Follow semantic versioning (e.g., 1.0.0). Each processed snapshot includes a manifest file for reproducibility.

## Manifest Template
A manifest file should accompany each processed dataset snapshot. It records provenance and reproducibility information. Example template:

```json
{
  "version": "0.1.0",
  "created_at": "2025-11-14T12:00:00Z",
  "script": "src/data/build_dataset.py",
  "git_commit": "abc123def",
  "preprocessing": {
    "remove_empty_repos": true,
    "min_files": 5
  },
  "rows": 12345,
  "checksum": "sha256:...",
  "notes": "Edit fields to match the produced snapshot. Save alongside the processed dataset."
}
```

- `version`: Semantic version of the snapshot
- `created_at`: ISO8601 timestamp
- `script`: Path to the script used for processing
- `git_commit`: Commit hash of the code used
- `preprocessing`: Dictionary of parameters and steps
- `rows`: Number of rows in the processed dataset
- `checksum`: SHA256 checksum of the main artifact
- `notes`: Optional notes or comments
