FROM postgres:14.5-bullseye
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
WORKDIR /usr/src/app
RUN apt update
RUN apt install python3 python3-pip -y
RUN apt-get install -y libpq-dev
RUN python -m pip install toml
RUN python -c 'import toml; c = toml.load("pyproject.toml"); print("\n".join(c["project"]["dependencies"]))' | python -m pip install -r /dev/stdin
RUN python -c 'import toml; c = toml.load("pyproject.toml"); print("\n".join(c["project"]["optional-dependencies"][$service_name]))' | python -m pip install -r /dev/stdin
COPY $WHEEL_FILENAME ./
RUN pip3 install "$WHEEL_FILENAME"
COPY initialize_schema.sql /docker-entrypoint-initdb.d/
COPY .spt_db.config.local ./
HEALTHCHECK CMD spt db status --database-config-file .spt_db.config.local || exit 1
CMD ["postgres"]
