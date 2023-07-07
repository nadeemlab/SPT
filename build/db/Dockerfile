FROM postgres:14.5-bullseye
WORKDIR /usr/src/app
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y python3 python3-pip libpq-dev && rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install psycopg2==2.9.6
RUN python3 -m pip install adiscstudies==0.11.0
RUN python3 -m pip install numba==0.57.0
RUN python3 -m pip install attrs==23.1.0
RUN python3 -m pip install pandas==2.0.2
RUN python3 -m pip install pyshp==2.2.0
RUN python3 -m pip install pydantic==1.10.11
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
ENV service_name $service_name
COPY $WHEEL_FILENAME ./
RUN python3 -m pip install "$WHEEL_FILENAME"
COPY initialize_schema.sql /docker-entrypoint-initdb.d/
COPY .spt_db.config.container ./
HEALTHCHECK CMD spt db status --database-config-file .spt_db.config.container || exit 1
CMD ["postgres", "-h", "0.0.0.0"]
