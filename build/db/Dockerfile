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
RUN python3 -m pip install --break-system-packages psycopg==3.1.19
RUN python3 -m pip install --break-system-packages adiscstudies==0.11.0
RUN python3 -m pip install --break-system-packages numba==0.59.1
RUN python3 -m pip install --break-system-packages attrs==23.2.0
RUN python3 -m pip install --break-system-packages pandas==2.2.2
RUN python3 -m pip install --break-system-packages pyshp==2.3.1
RUN python3 -m pip install --break-system-packages pydantic==2.7.2
RUN python3 -m pip install --break-system-packages anndata==0.10.9
RUN python3 -m pip install --break-system-packages squidpy==1.5.0
RUN python3 -m pip install --break-system-packages termplotlib==0.3.9
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
