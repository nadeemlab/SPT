FROM ubuntu:20.04
LABEL version="{{workflow-version}}"
LABEL service_name="workflow"
WORKDIR /usr/src/app
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get -y install python3-dev
RUN apt-get update && apt-get -y install python3-pip
COPY ../../setup.py ./
COPY ../../pyproject.toml ./
ADD ../../spatialprofilingtoolbox/ ./spatialprofilingtoolbox
RUN pip install ".[workflow]"
