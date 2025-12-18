FROM pytorch/pytorch:2.8.0-cuda12.9-cudnn9-runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

COPY environment/environment-base.yaml .

RUN conda env update -n base --file environment-base.yaml && conda clean -afy

RUN pip install --no-cache-dir pre-commit

EXPOSE 8888

CMD ["bash"]