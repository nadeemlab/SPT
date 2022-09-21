FROM python:3.9-slim
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
COPY $WHEEL_FILENAME ./
RUN pip3 install "$WHEEL_FILENAME[$service_name]"
COPY ./app /app
ENV API_SERVER_PORT=8080
HEALTHCHECK CMD curl --fail http://localhost:${API_SERVER_PORT}/ || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "debug"]
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "debug", "--workers", "9"]