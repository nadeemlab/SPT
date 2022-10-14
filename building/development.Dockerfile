FROM ubuntu:22.04
ARG WHEEL_FILENAME
RUN apt update
RUN apt install python3 python3-pip -y
RUN apt install python3-venv -y
RUN apt-get install -y libpq-dev
RUN apt install curl -y
RUN apt install openjdk-11-jdk -y
WORKDIR /usr/src/app
ENV PATH="/usr/src/app:$PATH" 
RUN curl -s https://get.nextflow.io | bash
COPY README.md .
COPY pyproject.toml .
RUN python3 -m pip install toml
RUN python3 -c 'import toml; c = toml.load("pyproject.toml"); print("\n".join(c["project"]["dependencies"]))' | python3 -m pip install -r /dev/stdin
RUN python3 -c 'import toml; c = toml.load("pyproject.toml"); print("\n".join(c["project"]["optional-dependencies"]["all"]))' | python3 -m pip install -r /dev/stdin
RUN python3 -m pip install build
COPY spatialprofilingtoolbox spatialprofilingtoolbox
RUN python3 -m build
RUN pip3 install --no-deps "dist/$WHEEL_FILENAME"
