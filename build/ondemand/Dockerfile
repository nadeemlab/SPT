FROM python:3.13-slim
ENV DEBIAN_FRONTEND=noninteractive
ARG PIP_NO_CACHE_DIR=1
RUN apt update && apt install -y gcc g++ libpq-dev && apt-get clean
WORKDIR /usr/src/app
RUN apt install -y libgdal-dev && apt-get clean
RUN python -m pip install --ignore-requires-python spatialdata==0.3.0
RUN python -m pip install toml
COPY pyproject.toml.unversioned .
RUN python -c 'import toml; c = toml.load("pyproject.toml.unversioned"); print("\n".join(c["project"]["dependencies"]))' | python -m pip install -r /dev/stdin
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
