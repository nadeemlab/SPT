FROM nadeemlab-development/spt-development-prereqs:latest
ARG WHEEL_FILENAME
COPY pyproject.toml .
COPY spatialprofilingtoolbox spatialprofilingtoolbox
RUN python -m build
RUN python -m pip install --no-deps "dist/$WHEEL_FILENAME"
