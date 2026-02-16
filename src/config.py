from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    github_token: str = Field(
        ...,
        description="GitHub Personal Access Token",
        min_length=1,
    )
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
    languages: list[str] = Field(
        default=["Python", "JavaScript", "TypeScript", "Go", "Rust"],
        description="Programming languages to filter by",
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
    retry_attempts: int = Field(
        default=3,
        ge=1,
        description="Number of retry attempts for failed API calls",
    )
    data_dir: Path = Field(
        default=Path("data"),
        description="Base directory for all data",
    )
    output_dir: Path = Field(
        default=Path("data/raw"),
        description="Directory for raw extracted data",
    )
    logs_dir: Path = Field(
        default=Path("logs"),
        description="Directory for extraction logs",
    )
    dataset_format: Literal["jsonl", "parquet", "csv"] = Field(
        default="parquet",
        description="Output format for dataset",
    )
    random_seed: int = Field(
        default=42,
        description="Random seed for reproducible sampling",
    )

    @field_validator("github_token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        """Ensure token is not a placeholder."""
        if v in ("your_token_here", "ghp_placeholder", ""):
            raise ValueError(
                "GitHub token not set. Create .env with GITHUB_TOKEN=<your_token>"
            )
        return v

    @field_validator("output_dir", "logs_dir")
    @classmethod
    def create_dirs(cls, v: Path) -> Path:
        """Ensure output directories exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("max_size_kb")
    @classmethod
    def validate_size_range(cls, v: int | None, info) -> int | None:
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
