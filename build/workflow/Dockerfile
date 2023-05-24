FROM python:3.9-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /usr/src/app
RUN python -m pip install psycopg2==2.9.3
RUN python -m pip install adiscstudies==0.11.0
RUN python -m pip install numba==0.56.4
RUN python -m pip install matplotlib==3.5.3
RUN python -m pip install umap-learn==0.5.3
RUN python -m pip install numpy==1.22.3
RUN python -m pip install scipy==1.8.0
RUN python -m pip install scikit-learn==1.1.2
RUN python -m pip install pyshp==2.2.0
RUN python -m pip install "pandas>=1.1.5"
RUN python -m pip install Jinja2==3.0.1
RUN python -m pip install tabulate==0.8.10
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
ENV service_name $service_name
COPY $WHEEL_FILENAME ./
RUN python -m pip install "$WHEEL_FILENAME"
RUN echo "workflow container is ready to work"
