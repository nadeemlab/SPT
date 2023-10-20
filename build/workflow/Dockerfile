FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y gcc libpq-dev
WORKDIR /usr/src/app
RUN apt install software-properties-common -y
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt update
RUN apt install python3.11 -y
RUN apt install python3.11-dev -y
RUN apt install python3.11-venv -y
RUN apt install python3.11-distutils -y
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 && python3.11 -m ensurepip
RUN python3.11 -m pip install dgl-cu117 dglgo -f https://data.dgl.ai/wheels/repo.html
RUN python3.11 -m pip install psycopg2==2.9.6
RUN python3.11 -m pip install adiscstudies==0.11.0
RUN python3.11 -m pip install numba==0.57.0
RUN python3.11 -m pip install attrs==23.1.0
RUN python3.11 -m pip install tables
RUN python3.11 -m pip install cg-gnn
RUN python3.11 -m pip install matplotlib==3.7.1
RUN python3.11 -m pip install umap-learn==0.5.3
RUN python3.11 -m pip install numpy==1.24.3
RUN python3.11 -m pip install scipy==1.10.1
RUN python3.11 -m pip install scikit-learn==1.2.2
RUN python3.11 -m pip install pyshp==2.2.0
RUN python3.11 -m pip install pandas==2.0.2
RUN python3.11 -m pip install Jinja2==3.1.2
RUN python3.11 -m pip install tabulate==0.8.10
RUN python3.11 -m pip install Pillow==9.5.0
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
ENV service_name $service_name
COPY $WHEEL_FILENAME ./
RUN python3.11 -m pip install "$WHEEL_FILENAME"
RUN echo "workflow container is ready to work"
