FROM ubuntu:20.04

LABEL version="0.7.18"

WORKDIR /usr/src/app

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get -y install python3-dev
RUN apt-get update && apt-get -y install python3-pip

RUN pip install --no-cache-dir Cython==0.29.23
RUN pip install --no-cache-dir matplotlib==3.4.2
RUN pip install --no-cache-dir pyparsing==2.4.7
RUN pip install --no-cache-dir python-dateutil==2.8.1
RUN pip install --no-cache-dir pytz==2021.1
RUN pip install --no-cache-dir six==1.16.0
RUN pip install --no-cache-dir networkx==2.5.1
RUN pip install --no-cache-dir POT==0.7.0
RUN pip install --no-cache-dir seaborn==0.11.1
RUN pip install --no-cache-dir plotly==5.1.0
RUN pip install --no-cache-dir kaleido==0.2.1
RUN pip install --no-cache-dir numpy==1.21.0
RUN pip install --no-cache-dir pandas==1.3.3
RUN pip install --no-cache-dir scipy==1.7.1
RUN pip install --no-cache-dir scikit-learn==0.24.1

COPY requirements.txt ./
COPY LICENSE.md ./
COPY setup.py ./
COPY pyproject.toml ./
ADD spatialprofilingtoolbox/ ./spatialprofilingtoolbox
RUN pip install .

ENV DEBUG=1
