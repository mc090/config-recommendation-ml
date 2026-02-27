# Dockerfile
FROM pytorch/pytorch:2.8.0-cuda12.9-cudnn9-runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    && \
    rm -rf /var/lib/apt/lists/*

# Copy environment files
COPY environment/environment-base.yaml ./environment/

# Update base environment with your dependencies
# NOTE: Using base environment since pytorch image already has conda base configured
RUN conda env update -n config-ml --file environment/environment-base.yaml && \
    conda clean -afy

# Install development tools
RUN pip install --no-cache-dir pre-commit

# Copy project files
COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/

# Install project in editable mode
# This makes 'from src.config import Settings' work
RUN pip install --no-cache-dir -e .

# Create directories for data and logs
RUN mkdir -p data/raw logs

# Set Python to unbuffered mode (see logs in real-time)
ENV PYTHONUNBUFFERED=1

# Set PYTHONPATH as backup (editable install should handle this)
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose Jupyter port
EXPOSE 8888

# Default command: bash for interactive use
CMD ["bash"]