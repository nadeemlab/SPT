FROM python:3.13-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y gcc g++ libpq-dev curl && apt-get clean
WORKDIR /usr/src/app
RUN apt install -y libgdal-dev && apt-get clean

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

RUN mkdir -p /tmp/pip-cache
ENV PIP_CACHE_DIR=/tmp/pip-cache

RUN python3.13 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml .
RUN --mount=type=cache,target=${PIP_CACHE_DIR} bash -c 'source /opt/venv/bin/activate && uv pip install --extra ondemand -r pyproject.toml'
COPY requirements.ondemand.txt .
RUN --mount=type=cache,target=${PIP_CACHE_DIR} bash -c 'source /opt/venv/bin/activate && uv pip install -r requirements.ondemand.txt'
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
ENV service_name=$service_name
COPY $WHEEL_FILENAME ./
RUN python -m pip install --no-deps "$WHEEL_FILENAME"
ENV API_SERVER_PORT=8016
ENTRYPOINT ["spt", "ondemand", "start"]
