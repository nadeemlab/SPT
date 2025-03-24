FROM python:3.13-slim
ENV DEBIAN_FRONTEND=noninteractive
ARG PIP_NO_CACHE_DIR=1
RUN apt update && apt install -y gcc g++ libpq-dev && apt-get clean
WORKDIR /usr/src/app
RUN apt install -y libgdal-dev && apt-get clean
COPY requirements.ondemand.txt .
RUN grep setuptools requirements.ondemand.txt | xargs python -m pip install
RUN python -m pip install -r requirements.ondemand.txt --no-build-isolation
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
