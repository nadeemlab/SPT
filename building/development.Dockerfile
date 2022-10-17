FROM ubuntu:22.04
ARG WHEEL_FILENAME
RUN apt update
RUN apt install python3 python3-pip -y
RUN apt install python3-venv -y
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN apt-get install -y libpq-dev
RUN apt install curl -y
RUN apt install openjdk-11-jdk -y
RUN apt install xxd
WORKDIR /usr/src/app
ENV PATH="/usr/src/app:$PATH" 
RUN curl -s https://get.nextflow.io | bash
COPY README.md .
COPY pyproject.toml .
RUN python -m pip install toml
RUN python -c 'import toml; c = toml.load("pyproject.toml"); print("\n".join(c["project"]["dependencies"]))' | python -m pip install -r /dev/stdin
RUN python -c 'import toml; c = toml.load("pyproject.toml"); print("\n".join(c["project"]["optional-dependencies"]["all"]))' | python -m pip install -r /dev/stdin
RUN python -m pip install build
COPY spatialprofilingtoolbox spatialprofilingtoolbox
RUN python -m build
RUN pip install --no-deps "dist/$WHEEL_FILENAME"
CMD bash 