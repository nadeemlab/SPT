FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y gcc libpq-dev curl && apt-get clean
ARG PIP_NO_CACHE_DIR=1
RUN python -m pip install psycopg==3.1.19
RUN python -m pip install adiscstudies==0.11.0
RUN python -m pip install numba==0.59.1
RUN python -m pip install attrs==23.2.0
RUN python -m pip install fastapi==0.111.0
RUN python -m pip install uvicorn==0.30.0
RUN python -m pip install pandas==2.2.2
RUN python -m pip install scipy==1.13.1
RUN python -m pip install numpy==1.26.4
RUN python -m pip install pyshp==2.3.1
RUN python -m pip install scikit-learn==1.5.0
RUN python -m pip install Pillow==9.5.0
RUN python -m pip install pydantic==2.7.2
RUN python -m pip install secure==0.3.0
RUN python -m pip install matplotlib==3.9.0
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
ENV service_name=$service_name
COPY $WHEEL_FILENAME ./
RUN pip3 install "$WHEEL_FILENAME"
ENV API_SERVER_PORT=8080
HEALTHCHECK CMD curl --fail http://localhost:${API_SERVER_PORT}/ || exit 1
CMD uvicorn app.main:app --app-dir /usr/local/lib/python3.11/site-packages/spatialprofilingtoolbox/apiserver/ --host 0.0.0.0 --port ${API_SERVER_PORT} --log-level debug
