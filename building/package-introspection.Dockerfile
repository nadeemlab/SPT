FROM python:3.9-slim
WORKDIR /usr/src/app
COPY README.md .
COPY pyproject.toml .
COPY spatialprofilingtoolbox spatialprofilingtoolbox
RUN python -m pip install jinja2
RUN python -m pip install --no-deps .
