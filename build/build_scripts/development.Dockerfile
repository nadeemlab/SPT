FROM nadeemlab-development/spt-development-prereqs:latest
ARG WHEEL_FILENAME
ARG PIP_NO_CACHE_DIR=1
COPY pyproject.toml .
COPY spatialprofilingtoolbox spatialprofilingtoolbox
RUN python -m build
RUN python -m pip install --no-deps "dist/$WHEEL_FILENAME"
