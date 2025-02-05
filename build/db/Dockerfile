FROM postgres:16.0-bookworm
WORKDIR /usr/src/app
ENV DEBIAN_FRONTEND=noninteractive
ARG PIP_NO_CACHE_DIR=1
RUN apt update && apt-get clean
RUN apt install python3 -y && apt-get clean
RUN apt install python3-dev -y && apt-get clean
RUN apt install python3-venv -y && apt-get clean
RUN apt install python3-pip -y && apt-get clean
RUN apt install -y libpq-dev && apt-get clean
RUN apt install -y libgdal-dev && apt-get clean
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
ENV service_name $service_name
COPY $WHEEL_FILENAME ./
RUN python3 -m pip install --break-system-packages "$WHEEL_FILENAME"
COPY .spt_db.config.container ./
RUN localedef -i en_US -f UTF-8 en_US.UTF-8
HEALTHCHECK CMD spt db status --database-config-file .spt_db.config.container || exit 1
CMD ["postgres", "-h", "0.0.0.0"]
