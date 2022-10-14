FROM python:3.9-slim
ARG WHEEL_FILENAME
RUN apt-get update
RUN apt-get -y install gcc
RUN apt-get install -y libpq-dev
WORKDIR /usr/src/app
COPY README.md .
COPY pyproject.toml .
RUN python -m pip install toml
RUN python -c 'import toml; c = toml.load("pyproject.toml"); print("\n".join(c["project"]["dependencies"]))' | python -m pip install -r /dev/stdin
RUN python -c 'import toml; c = toml.load("pyproject.toml"); print("\n".join(c["project"]["optional-dependencies"]["all"]))' | python -m pip install -r /dev/stdin
RUN python -m pip install build
COPY spatialprofilingtoolbox spatialprofilingtoolbox
RUN python -m build
RUN pip3 install --no-deps "dist/$WHEEL_FILENAME"
