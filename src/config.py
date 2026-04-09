"""Configuration management for the config-recommendation-ml project."""

from pathlib import Path
from typing import Any

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    github_token: str = Field(
        ...,
        description="GitHub Personal Access Token",
        min_length=1,
    )

    # Github search parameters
    min_stars: int = Field(
        default=10,
        ge=0,
        description="Minimum number of stars for repository inclusion",
    )
    max_repos: int = Field(
        default=1000,
        gt=0,
        description="Maximum number of repositories to extract",
    )
    exclude_forks: bool = Field(
        default=True,
        description="Exclude forked repositories",
    )
    exclude_archived: bool = Field(
        default=True,
        description="Exclude archived repositories",
    )
    max_time_since_update_days: int = Field(
        default=365,
        ge=0,
        description="Exclude repositories not updated in the last N days",
    )
    min_size_kb: int = Field(
        default=10,
        ge=0,
        description="Minimum repository size in KB",
    )
    max_size_kb: int | None = Field(
        default=500_000,  # 500 MB
        description="Maximum repository size in KB (None = no limit)",
    )

    # API rate limiting parameters
    requests_per_minute: int = Field(
        default=60,
        gt=0,
        le=5000,
        description="Max GitHub REST API requests per minute (for Trees API, etc.). "
        "Note: Search API has hard limit of 30 req/min regardless of this setting.",
    )
    min_request_delay: float = Field(
        default=1.0,
        ge=0.0,
        le=10.0,
        description="Minimum delay between GitHub API requests (seconds). "
        "Prevents secondary rate limits triggered by request bursts. "
        "Recommended: 1.0s for safety, reduce to 0.5s if needed.",
    )

    # GitHub Search API has a hard limit of 30 requests/minute
    GITHUB_SEARCH_API_LIMIT: int = 30

    # Output paths
    raw_data_path: Path = Field(
        default=Path("data/raw/raw_metadata.json"),
        description="Path to save raw extracted metadata",
    )
    structure_path: Path = Field(
        default=Path("data/interim/structure.json"),
        description="Path to save extracted structure data",
    )
    structure_enriched_path: Path = Field(
        default=Path("data/interim/structure_enriched.json"),
        description="Path to save content-enriched structure data",
    )
    computed_features_path: Path = Field(
        default=Path("data/interim/computed_features.json"),
        description="Path to save computed features for modeling",
    )
    dataset_output_dir: Path = Field(
        default=Path("data/processed"),
        description="Base directory for processed datasets",
    )
    logs_dir: Path = Field(
        default=Path("logs"),
        description="Directory for extraction logs",
    )
    pipeline_init_snapshot: Path = Field(
        default=Path("logs/pipeline_init.json"),
        description="Path to save pipeline initialization snapshot",
    )

    # Sampling parameters
    random_seed: int = Field(
        default=90,
        description="Random seed for reproducible sampling",
    )

    # Dataset stratification
    stratify_labels: list[str] = Field(
        default=["has_pyproject_toml", "has_dockerfile", "has_github_actions"],
        description="Label columns to use for multi-label stratification in splits",
    )

    # Variant generation configuration
    variant_label_columns: list[str] = Field(
        default=[
            "has_pyproject_toml",
            "has_dockerfile",
            "has_github_actions",
            "has_requirements_txt",
            "has_conda_env_file",
            "has_docker_compose",
            "has_precommit_config",
            "has_setup_py",
            "has_tox_ini",
            "has_makefile",
        ],
        description="Label columns used by dataset-variant generation scripts",
    )
    variant_correlation_thresholds: list[float] = Field(
        default=[0.70, 0.60],
        description="Correlation thresholds for generating correlation-pruned variants",
    )
    variant_correlation_pvalue_threshold: float = Field(
        default=0.05,
        gt=0.0,
        le=1.0,
        description="P-value threshold for correlation significance in variant pruning",
    )
    variant_dominance_threshold: float = Field(
        default=0.80,
        gt=0.0,
        le=1.0,
        description="Dominance-ratio threshold for dominance-based variant pruning",
    )
    variant_low_variance_selected_features: list[str] = Field(
        default=["avg_files_per_dir", "avg_nb_cell_count", "has_license"],
        description="Features with low variance to drop in the low-variance variant",
    )

    # Dataset versioning
    dataset_version: str | None = Field(
        default=None,
        description=(
            "Manual override for dataset version (e.g., '2.0.0')."
            "If None, auto-increments patch version.",
        ),
    )

    @field_validator("github_token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        """Ensure token is not a placeholder."""
        if v in ("your_token_here", "ghp_placeholder", ""):
            raise ValueError(
                "GitHub token not set. Set the GITHUB_TOKEN environment variable or"
                " provide a valid token in the .env file.",
            )
        return v

    @field_validator(
        "raw_data_path",
        "structure_path",
        "structure_enriched_path",
        "computed_features_path",
        "logs_dir",
        "pipeline_init_snapshot",
    )
    @classmethod
    def create_dir(cls, v: Path) -> Path:
        """Ensure parent directory for the raw output file exists."""
        v.parent.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("max_size_kb")
    @classmethod
    def validate_size_range(cls, v: int | None, info: ValidationInfo) -> int | None:
        """Ensure max_size >= min_size."""
        if v is not None and "min_size_kb" in info.data:
            min_size = info.data["min_size_kb"]
            if v < min_size:
                raise ValueError(f"max_size_kb ({v}) < min_size_kb ({min_size})")
        return v

    @field_validator("variant_correlation_thresholds")
    @classmethod
    def validate_variant_correlation_thresholds(cls, v: list[float]) -> list[float]:
        """Ensure correlation thresholds are in (0, 1]."""
        if not v:
            raise ValueError("variant_correlation_thresholds cannot be empty")
        for threshold in v:
            if threshold <= 0.0 or threshold > 1.0:
                raise ValueError(
                    "variant_correlation_thresholds values must be in (0, 1]"
                )
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    def to_reproducible_dict(self) -> dict[str, Any]:
        """Export config to JSON-serializable dict, excluding secrets."""
        data = self.model_dump()
        data.pop("github_token", None)

        # Convert all Path fields to strings for JSON serialization
        for key, value in data.items():
            if isinstance(value, Path):
                data[key] = str(value)

        return data


settings = Settings()
