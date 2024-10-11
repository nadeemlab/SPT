FROM nadeemlab-development/spt-development-prereqs:latest
ARG WHEEL_FILENAME
ARG PIP_NO_CACHE_DIR=1
COPY pyproject.toml .
COPY spatialprofilingtoolbox spatialprofilingtoolbox
ENV SPT_TESTING_MODE=1
RUN python -m build
RUN python -m pip install --no-deps "dist/$WHEEL_FILENAME"
