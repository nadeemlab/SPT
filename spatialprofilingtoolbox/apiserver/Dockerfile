FROM python:3.9-slim

LABEL version="{{workflow-version}}"
LABEL service_name="workflow"

WORKDIR /usr/src/app

COPY ./requirements.txt /code/requirements.txt

RUN pip3 install --no-cache-dir --upgrade -r /code/requirements.txt

{{install requirements}}

# Glean above from new declarative style requirements ...

COPY ./app ./
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "debug", "--workers", "9"]
