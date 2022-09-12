FROM postgres:14.5-bullseye
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
WORKDIR /usr/src/app
COPY $WHEEL_FILENAME ./
RUN pip3 install "$WHEEL_FILENAME[$service_name]"
