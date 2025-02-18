FROM python:3.13-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y gcc libpq-dev curl && apt-get clean
ARG PIP_NO_CACHE_DIR=1
COPY requirements.txt /usr/local/lib/python3.13/site-packages/spatialprofilingtoolbox/apiserver/app/
COPY requirements.apiserver.txt .
RUN python -m pip install -r requirements.apiserver.txt
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
COPY $WHEEL_FILENAME ./
RUN python -m pip install --no-deps "$WHEEL_FILENAME"
ENV API_SERVER_PORT=8080
HEALTHCHECK CMD curl --fail http://localhost:${API_SERVER_PORT}/ || exit 1
RUN TZ=America/New_York date +"%A %B %d %Y %l:%M %p %Z" >/build_datetime.txt
CMD echo "Container built at:" $(cat /build_datetime.txt) && uvicorn app.main:app --root-path /api --workers 4 --app-dir /usr/local/lib/python3.13/site-packages/spatialprofilingtoolbox/apiserver/ --host 0.0.0.0 --port ${API_SERVER_PORT} --log-level debug
