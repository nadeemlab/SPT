FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive
ARG PIP_NO_CACHE_DIR=1
RUN apt update && apt install -y gcc g++ libpq-dev && apt-get clean
WORKDIR /usr/src/app
RUN apt install -y libgdal-dev && apt-get clean
RUN python -m pip install psycopg==3.1.19
RUN python -m pip install adiscstudies==0.11.0
RUN python -m pip install numba==0.59.0
RUN python -m pip install attrs==23.2.0
RUN python -m pip install pandas==2.2.2
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
ENV service_name $service_name
COPY $WHEEL_FILENAME ./
RUN python -m pip install "$WHEEL_FILENAME"
ENTRYPOINT ["spt", "watcher", "start"]
