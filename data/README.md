# GitHub Python Repository Structure Dataset

## Overview
This dataset contains information about the structure of Python projects that was collected from popular public repositories on GitHub.  
Its purpose is to help develop machine learning models that can suggest which configuration files (e.g., `Dockerfile`, `pyproject.toml`, `.pre-commit-config.yaml`) should be added to a project based on its existing structure.

The base version of this dataset is intentionally redundant - later preprocessing steps (feature engineering, dimensionality reduction, attribute selection) will refine it.

---

## Data Sources
- GitHub public repositories retrieved using the GitHub API.  
- Repository selection criteria:

⚠️ **Disclaimer**: This dataset only contains file structure metadata. It does not redistribute source code content.

---

## Dataset Schema
Each entry in the dataset corresponds to one GitHub repository and follows this schema:

```json
{
  // Attributes
  "repo_url": "string",             // Link to the GitHub repository
  "stars": "int",                   // Number of stars in GitHub repository
  "forks": "int",                   // Number of forks in GitHub repository
  "created_at": "Date",             // Date of creation (format: dd-MM-YYYY)
  "last_updated": "Date",           // Date of last update (format: dd-MM-YYYY)
  "num_files": "int",               // Total number of files
  "num_py_files": "int",            // Number of Python files
  "num_js_files": "int",            // Number of JavaScript files
  "num_ts_files": "int",            // Number of TypeScript files
  "num_html_files": "int",          // Number of HTML files
  "num_css_files": "int",           // Number of CSS files
  "num_json_files": "int",          // Number of JSON files
  "num_sh_files": "int",            // Number of Shell files
  "num_test_files": "int",          // Number of test files
  "num_docs_files": "int",          // Number of documentation files (.md or .rst)
  "num_notebooks": "int",           // Number of Jupyter Notebook files
  "other_extensions_count": "int",  // Number of files with other extentions than specified above    
  "has_tests_dir": "bool",          // Checks for /tests directory
  "num_dirs": "int",                // Total number of directories
  "top_level_dirs": ["string"],     // List of top-level directories 
  "avg_files_per_dir": "int",       // Average number of files per directory
  "avg_py_file_len": "int",         // Average length of Python file
  "avg_nb_file_len": "int",         // Average length of Jupyter Notebook file
  "avg_docs_file_len": "int",       // Average length of documentation file
  "num_dependencies": "int",        // Number of dependencies
  "repo_age_days": "int",           // Days passed from repository creation
  "recent_activity_days": "int",    // Days passed from latest change in repository

  // Labels
  "has_requirements_txt": "bool",   // Checks for requirements.txt
  "has_conda_env": "bool",          // Checks for environment*.yaml
  "has_pyproject_toml": "bool",     // Checks for pyproject.toml
  "has_pyproject_lock": "bool",     // Checks for pyproject.lock
  "has_github_actions": "bool",     // Checks for .github/workflows/
  "has_dockerfile": "bool",         // Checks for Dockerfile
  "has_docker_compose": "bool",     // Checks for docker-compose.yaml
  "has_precommit_config": "bool"    // Checks for .pre-commit-config.yaml
}
```

---

## Files structure
 ([see main project README](../README.md)).