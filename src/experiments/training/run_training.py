"""CLI entrypoint for the training pipeline."""

from src.experiments.training.pipeline import run_training_experiment
from src.logger import get_logger

logger = get_logger(__name__)


def run_training() -> None:
    """Run model training based on settings-driven configuration."""
    output_dir = run_training_experiment()
    logger.info("Training run completed. Output: %s", output_dir)


if __name__ == "__main__":
    run_training()
