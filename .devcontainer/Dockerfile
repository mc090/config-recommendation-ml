# Użyj oficjalnego obrazu Pythona jako bazy
FROM python:3.11-slim

# Ustaw zmienną środowiskową
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Zainstaluj systemowe zależności
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Utwórz katalog roboczy
WORKDIR /workspace
RUN useradd -m vscode
USER vscode
