FROM python:3.10-slim AS base

# Useful packages to handle images, fonts etc.
RUN apt-get -y update && \
    apt-get -y install --no-install-recommends git curl make cmake \
    xz-utils pkg-config build-essential \
    mesa-common-dev libgl1-mesa-dev libglu1-mesa-dev \
    libxi-dev libxrandr-dev libfreetype6-dev libfontconfig1-dev \
    libjpeg-dev libcairo2-dev liblcms2-dev libboost-dev libopenjp2-7-dev \
    libopenjp2-tools

ENV PATH="/root/.local/bin:$PATH"
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV APP_DIR="/application"
WORKDIR $APP_DIR

COPY pyproject.toml uv.lock README.md ./

RUN uv venv

RUN uv sync --frozen --no-install-project

COPY ./app ${APP_DIR}/app

RUN uv sync --frozen

ENV DEBUG=false

EXPOSE 9000

CMD [".venv/bin/python", "-m", "app.main"]
