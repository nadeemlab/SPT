FROM pytorch/pytorch:1.13.0-cuda11.6-cudnn8-runtime
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /usr/src/app
RUN python -m pip install dgl-cu116 dglgo -f https://data.dgl.ai/wheels/repo.html
RUN python -m pip install psycopg2==2.9.3
RUN python -m pip install adiscstudies==0.11.0
RUN python -m pip install numba==0.56.4
RUN python -m pip install cg-gnn
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
ENV service_name $service_name
COPY $WHEEL_FILENAME ./
RUN python -m pip install "$WHEEL_FILENAME"
