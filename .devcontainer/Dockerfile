FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    vim \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces
RUN useradd -m vscode
USER vscode
