FROM python:3.9-slim
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
RUN apt-get update
RUN apt-get -y install gcc
RUN apt-get install -y libpq-dev
RUN python -m pip install toml
RUN python -c 'import toml; c = toml.load("pyproject.toml"); print("\n".join(c["project"]["dependencies"]))' | python -m pip install -r /dev/stdin
RUN python -c 'import toml; c = toml.load("pyproject.toml"); print("\n".join(c["project"]["optional-dependencies"][$service_name]))' | python -m pip install -r /dev/stdin
COPY $WHEEL_FILENAME ./
RUN pip3 install "$WHEEL_FILENAME"
COPY ./app /app
ENV API_SERVER_PORT=8080
HEALTHCHECK CMD curl --fail http://localhost:${API_SERVER_PORT}/ || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "debug"]
