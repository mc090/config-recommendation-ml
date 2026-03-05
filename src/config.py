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
    requests_per_minute: int = Field(
        default=30,
        gt=0,
        le=5000,
        description="Max GitHub API requests per minute",
    )

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
    logs_dir: Path = Field(
        default=Path("logs"),
        description="Directory for extraction logs",
    )

    # Sampling parameters
    random_seed: int = Field(
        default=90,
        description="Random seed for reproducible sampling",
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

    @field_validator("raw_data_path")
    @classmethod
    def create_raw_data_parent_dir(cls, v: Path) -> Path:
        """Ensure parent directory for the raw output file exists."""
        v.parent.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("structure_path")
    @classmethod
    def create_structure_parent_dir(cls, v: Path) -> Path:
        """Ensure parent directory for the structure output file exists."""
        v.parent.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("structure_enriched_path")
    @classmethod
    def create_structure_enriched_parent_dir(cls, v: Path) -> Path:
        """Ensure parent directory for the enriched structure output file exists."""
        v.parent.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("logs_dir")
    @classmethod
    def create_logs_dir(cls, v: Path) -> Path:
        """Ensure logs directory exists."""
        v.mkdir(parents=True, exist_ok=True)
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
