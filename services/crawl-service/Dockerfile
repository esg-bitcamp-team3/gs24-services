# Build Stage
FROM python:3.11-slim AS build

# Set the working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        curl \
        build-essential \
        chromium \
        chromium-driver \
        fonts-nanum fonts-nanum-coding fonts-nanum-extra \
        ca-certificates \
        libnss3 \
        libxss1 \
        libappindicator3-1 \
        libatk-bridge2.0-0 \
        libgtk-3-0 \
        libx11-xcb1 \
        libxcb1 \
        libdbus-1-3

# install poetry to manage python dependencies
RUN curl -sSL https://install.python-poetry.org | python3 - --version 2.1.0

ENV PATH="$POETRY_HOME/bin:$PATH"

# install python dependencies
COPY pyproject.toml poetry.lock /app/

RUN poetry config virtualenvs.create false && poetry install --only main --no-root

RUN pip install openpyxl

RUN pip install matplotlib

RUN pip install seaborn matplotlib

# copy project
COPY . /app

# run at port 8000
EXPOSE 8000

CMD ["poetry", "run", "gunicorn", "crawl_service.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "180"]

# services/crawl-service/Dockerfile
#FROM python:3.11
#
## 시스템 패키지 설치
#RUN apt-get update && apt-get install -y \
#    build-essential \
#    curl \
#    git \
#    wget \
#    libglib2.0-0 \
#    libsm6 \
#    libxext6 \
#    libxrender-dev \
#    && rm -rf /var/lib/apt/lists/*
#
## Poetry 설치
#ENV POETRY_VERSION=1.8.2
#RUN curl -sSL https://install.python-poetry.org | python3 - && \
#    ln -s /root/.local/bin/poetry /usr/local/bin/poetry
#
#WORKDIR /app
#
## pyproject.toml과 poetry.lock 복사
#COPY pyproject.toml poetry.lock* /app/
#
## 의존성 설치
#RUN poetry config virtualenvs.create false && \
#    poetry install --no-interaction --no-ansi
#
## 전체 프로젝트 복사
#COPY . /app/
#
## 포트 설정 및 실행
#EXPOSE 8000
#CMD ["gunicorn", "crawl_service.wsgi:application", "--bind", "0.0.0.0:8000"]
