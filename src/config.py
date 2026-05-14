"""Configuration management for the config-recommendation-ml project."""

from pathlib import Path
from typing import Any

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.experiments.training.enums import (
    DecisionTreeCriterion,
    GradientBoostingCriterion,
    HiddenActivation,
    ModelFamily,
    NeuralOptimizer,
    RandomForestMaxFeatures,
    SvmGamma,
    SvmKernel,
    TrainingMetric,
)


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
    training_output_dir: Path = Field(
        default=Path("logs/training"),
        description="Directory for training artifacts",
    )

    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Log level for project loggers (DEBUG/INFO/WARNING/ERROR/CRITICAL)",
    )
    third_party_log_level: str = Field(
        default="WARNING",
        description="Log level for noisy third-party libraries",
    )
    log_terse_console: bool = Field(
        default=True,
        description="Use concise console logging while keeping detailed file logs",
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
    variant_selected_features_for_pruning: list[str] = Field(
        default=["avg_files_per_dir", "avg_nb_cell_count", "has_license"],
        description="Features with low variance to drop in the low-variance variant",
    )

    # Training configuration
    training_enabled_model_families: list[ModelFamily] = Field(
        default=[
            ModelFamily.DECISION_TREE,
            ModelFamily.RANDOM_FOREST,
            ModelFamily.GRADIENT_BOOSTING,
            ModelFamily.SVM,
            ModelFamily.NEURAL_NETWORK,
        ],
        description="Model families to include in training runs",
    )
    training_cv_folds: int = Field(
        default=10,
        ge=2,
        description="Number of stratified CV folds",
    )
    training_variant_names: list[str] = Field(
        default=["original"],
        description="Dataset variant names to train",
    )
    training_stratify_label_columns: list[str] = Field(
        default=["has_pyproject_toml", "has_dockerfile", "has_github_actions"],
        description="Boolean labels used to build multiclass combination target keys"
        " and stratified CV splits",
    )
    training_gridsearch_n_jobs: int = Field(
        default=-1,
        description="Number of parallel jobs for GridSearchCV",
    )
    training_metrics: list[TrainingMetric] = Field(
        default=[
            TrainingMetric.ACCURACY,
            TrainingMetric.BALANCED_ACCURACY,
            TrainingMetric.PRECISION_MACRO,
            TrainingMetric.PRECISION_MICRO,
            TrainingMetric.PRECISION_WEIGHTED,
            TrainingMetric.RECALL_MACRO,
            TrainingMetric.RECALL_MICRO,
            TrainingMetric.RECALL_WEIGHTED,
            TrainingMetric.F1_MACRO,
            TrainingMetric.F1_MICRO,
            TrainingMetric.F1_WEIGHTED,
        ],
        description="Metrics computed and tracked in CV training",
    )
    training_gridsearch_refit_metric: TrainingMetric = Field(
        default=TrainingMetric.F1_WEIGHTED,
        description="Metric key used by GridSearchCV for best-params refit selection",
    )
    training_mlflow_tracking_uri: str = Field(
        default="file:./logs/mlruns",
        description="MLflow tracking URI",
    )
    training_mlflow_experiment_name: str = Field(
        default="config-recommendation-training",
        description="MLflow experiment name for training runs",
    )

    # Decision tree grids
    training_dt_max_depth_values: list[int] = Field(
        default=[5, 10, 20],
        description="DecisionTreeClassifier max_depth grid",
    )
    training_dt_min_samples_split_values: list[int] = Field(
        default=[2, 5, 10],
        description="DecisionTreeClassifier min_samples_split grid",
    )
    training_dt_min_samples_leaf_values: list[int] = Field(
        default=[1, 2, 4],
        description="DecisionTreeClassifier min_samples_leaf grid",
    )
    training_dt_criterion_values: list[DecisionTreeCriterion] = Field(
        default=[DecisionTreeCriterion.GINI, DecisionTreeCriterion.ENTROPY],
        description="DecisionTreeClassifier criterion grid",
    )

    # Random forest grids
    training_rf_n_estimators_values: list[int] = Field(
        default=[50, 100],
        description="RandomForestClassifier n_estimators grid",
    )
    training_rf_max_depth_values: list[int] = Field(
        default=[10, 20],
        description="RandomForestClassifier max_depth grid",
    )
    training_rf_min_samples_split_values: list[int] = Field(
        default=[2, 5],
        description="RandomForestClassifier min_samples_split grid",
    )
    training_rf_min_samples_leaf_values: list[int] = Field(
        default=[1, 2],
        description="RandomForestClassifier min_samples_leaf grid",
    )
    training_rf_max_features_values: list[RandomForestMaxFeatures] = Field(
        default=[RandomForestMaxFeatures.SQRT, RandomForestMaxFeatures.LOG2],
        description="RandomForestClassifier max_features grid",
    )

    # Gradient boosting grids
    training_gb_n_estimators_values: list[int] = Field(
        default=[50, 100],
        description="GradientBoostingClassifier n_estimators grid",
    )
    training_gb_learning_rate_values: list[float] = Field(
        default=[0.05, 0.1],
        description="GradientBoostingClassifier learning_rate grid",
    )
    training_gb_max_depth_values: list[int] = Field(
        default=[3, 5],
        description="GradientBoostingClassifier base-estimator max_depth grid",
    )
    training_gb_subsample_values: list[float] = Field(
        default=[0.8, 1.0],
        description="GradientBoostingClassifier subsample grid",
    )
    training_gb_min_samples_leaf_values: list[int] = Field(
        default=[1, 2],
        description="GradientBoostingClassifier min_samples_leaf grid",
    )
    training_gb_criterion_values: list[GradientBoostingCriterion] = Field(
        default=[
            GradientBoostingCriterion.FRIEDMAN_MSE,
            GradientBoostingCriterion.SQUARED_ERROR,
        ],
        description="GradientBoostingClassifier criterion grid",
    )

    # SVM grids
    training_svm_c_values: list[float] = Field(
        default=[0.1, 1.0, 10.0],
        description="SVM C grid",
    )
    training_svm_kernel_values: list[SvmKernel] = Field(
        default=[SvmKernel.LINEAR, SvmKernel.RBF],
        description="SVM kernel grid",
    )
    training_svm_gamma_values: list[SvmGamma] = Field(
        default=[SvmGamma.SCALE, SvmGamma.AUTO],
        description="SVM gamma grid",
    )

    # Neural network grids
    training_nn_hidden_layer_multipliers: list[float] = Field(
        default=[1.0, 2.0],
        description="Hidden-size multipliers for single-hidden-layer neural network",
    )
    training_nn_alpha_values: list[float] = Field(
        default=[0.0001, 0.001],
        description="PyTorch optimizer weight_decay (L2) grid",
    )
    training_nn_solver_values: list[NeuralOptimizer] = Field(
        default=[NeuralOptimizer.ADAM],
        description="PyTorch optimizer names for neural-network training",
    )
    training_nn_hidden_activation_values: list[HiddenActivation] = Field(
        default=[HiddenActivation.RELU],
        description="PyTorch hidden-layer activation grid",
    )
    training_nn_learning_rate_init_values: list[float] = Field(
        default=[0.001],
        description="PyTorch optimizer learning-rate grid",
    )
    training_nn_batch_size_values: list[int] = Field(
        default=[32, 64],
        description="PyTorch batch-size grid",
    )
    training_nn_max_iter_values: list[int] = Field(
        default=[300],
        description="PyTorch training epochs grid",
    )

    # Dataset versioning
    dataset_version: str | None = Field(
        default=None,
        description="Manual override for dataset version (e.g., '2.0.0')."
        "If None, auto-increments patch version.",
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
        "training_output_dir",
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

    @field_validator("log_level", "third_party_log_level")
    @classmethod
    def validate_log_levels(cls, v: str) -> str:
        """Ensure configured log level names are valid."""
        supported = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        normalized = v.strip().upper()
        if normalized not in supported:
            raise ValueError(
                f"Unsupported log level '{v}'. Supported: {sorted(supported)}"
            )
        return normalized

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

    @field_validator("training_enabled_model_families")
    @classmethod
    def validate_training_enabled_model_families(
        cls, v: list[ModelFamily]
    ) -> list[ModelFamily]:
        """Ensure configured model families are provided."""
        if not v:
            raise ValueError("training_enabled_model_families cannot be empty")
        return v

    @field_validator("training_gridsearch_refit_metric")
    @classmethod
    def validate_training_gridsearch_refit_metric(
        cls, v: TrainingMetric, info: ValidationInfo
    ) -> TrainingMetric:
        """Ensure refit metric is present in configured training metrics."""
        metrics = info.data.get("training_metrics")
        if metrics and v not in metrics:
            raise ValueError(
                "training_gridsearch_refit_metric must be present in training_metrics"
            )
        return v

    @field_validator("training_metrics")
    @classmethod
    def validate_training_metrics(
        cls, v: list[TrainingMetric], info: ValidationInfo
    ) -> list[TrainingMetric]:
        """Ensure training metrics are non-empty and include refit metric."""
        if not v:
            raise ValueError("training_metrics cannot be empty")
        refit_metric = info.data.get("training_gridsearch_refit_metric")
        if refit_metric and refit_metric not in v:
            raise ValueError(
                "training_metrics must include training_gridsearch_refit_metric "
                f"('{refit_metric}')"
            )
        return v

    @field_validator("training_stratify_label_columns")
    @classmethod
    def validate_training_stratify_label_columns(cls, v: list[str]) -> list[str]:
        """Ensure stratification columns are provided."""
        if not v:
            raise ValueError("training_stratify_label_columns cannot be empty")
        return v

    @field_validator(
        "training_nn_hidden_layer_multipliers",
    )
    @classmethod
    def validate_training_nn_layer_multipliers(cls, v: list[float]) -> list[float]:
        """Ensure hidden-layer size multipliers are positive."""
        if not v:
            raise ValueError("NN hidden-layer multipliers cannot be empty")
        if any(multiplier <= 0 for multiplier in v):
            raise ValueError("NN hidden-layer multipliers must be > 0")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    def to_reproducible_dict(self) -> dict[str, Any]:
        """Export config to JSON-serializable dict, excluding secrets."""
        data = self.model_dump(mode="json")
        data.pop("github_token", None)
        return data


settings = Settings()
