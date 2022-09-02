FROM python:3.9-slim
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
WORKDIR /usr/src/app
COPY $WHEEL_FILENAME ./
RUN pip3 install "$WHEEL_FILENAME[$service_name]"
COPY ./app ./
COPY ./counts_service_client.py ./
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "debug", "--workers", "9"]
