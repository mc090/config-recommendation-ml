FROM continuumio/miniconda3:main

WORKDIR /app

COPY environment.yaml .

RUN conda env create -f environment.yaml

SHELL ["/bin/bash", "-c"]

RUN conda install -n config-recommendation-ml -c conda-forge ipykernel && \
    conda clean -afy

ENV PATH=/opt/conda/envs/config-recommendation-ml/bin:$PATH
ENV CONDA_DEFAULT_ENV=config-recommendation-ml

EXPOSE 8888

CMD ["bash"]
