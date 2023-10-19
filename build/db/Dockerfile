FROM postgres:16.0-bookworm
WORKDIR /usr/src/app
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt upgrade -y
RUN apt install python3 -y
RUN apt install python3-dev -y
RUN apt install python3-venv -y
RUN apt install python3-pip -y
RUN apt install -y libpq-dev -y
RUN python3 -m pip install --break-system-packages psycopg2==2.9.6
RUN python3 -m pip install --break-system-packages adiscstudies==0.11.0
RUN python3 -m pip install --break-system-packages numba==0.57.0
RUN python3 -m pip install --break-system-packages attrs==23.1.0
RUN python3 -m pip install --break-system-packages pandas==2.0.2
RUN python3 -m pip install --break-system-packages pyshp==2.2.0
RUN python3 -m pip install --break-system-packages pydantic==2.0.2
RUN python3 -m pip install --break-system-packages squidpy==1.3.0
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
ENV service_name $service_name
COPY $WHEEL_FILENAME ./
RUN python3 -m pip install --break-system-packages "$WHEEL_FILENAME"
COPY initialize_schema.sql /docker-entrypoint-initdb.d/
COPY .spt_db.config.container ./
HEALTHCHECK CMD spt db status --database-config-file .spt_db.config.container || exit 1
CMD ["postgres", "-h", "0.0.0.0"]
