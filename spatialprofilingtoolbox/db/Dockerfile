FROM postgres:14.5-bullseye
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
WORKDIR /usr/src/app
COPY $WHEEL_FILENAME ./
RUN pip3 install "$WHEEL_FILENAME[$service_name]"
COPY .spt_db.config.local ./
RUN spt db create-schema --database-config-file=.spt_db.config.local 
# Somehow do roles and granting etc
HEALTHCHECK CMD spt db status || exit 1
