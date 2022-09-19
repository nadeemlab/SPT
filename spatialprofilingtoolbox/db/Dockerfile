FROM postgres:14.5-bullseye
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
WORKDIR /usr/src/app
COPY $WHEEL_FILENAME ./
RUN apt update
RUN apt install python3 python3-pip -y
RUN pip3 install "$WHEEL_FILENAME[$service_name]"
COPY data_model/create_database_and_roles.sql /docker-entrypoint-initdb.d/
COPY .spt_db.config.local ./
HEALTHCHECK CMD spt db status --database-config-file .spt_db.config.local || exit 1
RUN postgres ; spt db create-schema --database-config-file .spt_db.config.local --setup-users
CMD ["postgres"]
