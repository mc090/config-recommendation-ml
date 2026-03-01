FROM pytorch/pytorch:2.8.0-cuda12.9-cudnn9-runtime

WORKDIR /workspaces/config-recommendation-ml

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    && \
    rm -rf /var/lib/apt/lists/*

COPY environment/environment-base.yaml ./environment/

RUN conda env update -n config-ml --file environment/environment-base.yaml && \
    conda clean -afy

RUN pip install --no-cache-dir pre-commit

COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir -e .

RUN mkdir -p data/raw logs

ENV PYTHONUNBUFFERED=1

ENV PYTHONPATH=/workspaces/config-recommendation-ml:$PYTHONPATH

EXPOSE 8888

CMD ["bash"]