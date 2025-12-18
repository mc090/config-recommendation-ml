# Contributing Guide

Thank you for your interest in contributing to this project!

## How to Contribute
- Fork the repository and create your branch from `main`.
- Follow the coding standards and use pre-commit hooks (see [.pre-commit-config.yaml](./.pre-commit-config.yaml)).
- Write clear, descriptive commit messages.
- Add or update tests as needed and run the test suite locally.
- Document your changes in relevant files (README, dataset card, etc.).
- Submit a pull request with a summary of your changes.

## Formatting & Linting
- The project uses `ruff` for linting and formatting. Run `ruff check .` and `ruff format .` before committing.
- Use the repo's `pre-commit` hooks which run ruff, tests, and other checks automatically.

## Environment Setup
- Use the provided Dev Container for reproducible development.
- Or create Conda environments using the environment YAMLs:
```bash
conda env create --name config-recommendation-ml --file environment/environment-base.yaml --file environment/environment-torch.yaml
conda activate config-recommendation-ml
```

## Testing Guidelines
- Run unit tests locally:
```bash
pytest tests/
```
- Ensure all tests pass and linters are clean before opening a PR.
- Add tests for new functionality and edge cases.

## Pull Request Checklist
- [ ] Updated/added tests
- [ ] Linting/formatting (`ruff`) passes
- [ ] Documentation updated (if applicable)
- [ ] CHANGELOG updated with a short note (if applicable)
- [ ] PR description explains the motivation and changes

## Issue Reporting
- Use GitHub Issues for bug reports, feature requests, and questions.
- Provide clear steps to reproduce, minimal examples, and environment details.

## Code of Conduct
- Be respectful and constructive in all interactions.

## License
- By contributing, you agree your work will be distributed under the MIT License.
