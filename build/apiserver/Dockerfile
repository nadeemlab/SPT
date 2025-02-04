FROM python:3.13-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y gcc libpq-dev curl && apt-get clean
ARG PIP_NO_CACHE_DIR=1
RUN python -m pip install psycopg==3.1.19
RUN python -m pip install adiscstudies==0.11.0
RUN python -m pip install attrs==23.2.0
RUN python -m pip install fastapi==0.111.0
RUN python -m pip install uvicorn==0.30.0
RUN python -m pip install pandas==2.2.3
RUN python -m pip install scipy==1.15.1
RUN python -m pip install numpy==2.2.2
RUN python -m pip install pyshp==2.3.1
RUN python -m pip install scikit-learn==1.6.1
RUN python -m pip install Pillow==11.1.0
RUN python -m pip install pydantic==2.10.6
RUN python -m pip install secure==0.3.0
RUN python -m pip install matplotlib==3.9.2
RUN python -m pip install anndata==0.10.9
RUN python -m pip install numba==0.61.0
RUN python -m pip install spatialdata==0.3.0
RUN python -m pip install squidpy==1.5.0
RUN python -m pip install zstandard==0.23.0
RUN python -m pip install PyJWT==2.10.1
RUN python -m pip install cryptography==44.0.0
RUN python -m pip install alembic==1.14.0
RUN python -m pip install sqlmodel==0.0.22
RUN python -m pip install SQLAlchemy==2.0.36
RUN python -m pip install Brotli==1.1.0
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
RUN TZ=America/New_York date +"%A %B %d %Y %l:%M %p %Z" >/build_datetime.txt
CMD echo "Container built at:" $(cat /build_datetime.txt) && uvicorn app.main:app --root-path /api --workers 4 --app-dir /usr/local/lib/python3.11/site-packages/spatialprofilingtoolbox/apiserver/ --host 0.0.0.0 --port ${API_SERVER_PORT} --log-level debug
