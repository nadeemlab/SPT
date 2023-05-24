FROM python:3.9-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y gcc libpq-dev curl && rm -rf /var/lib/apt/lists/*
RUN python -m pip install psycopg2==2.9.3
RUN python -m pip install adiscstudies==0.11.0
RUN python -m pip install numba==0.56.4
RUN python -m pip install "fastapi>=0.68.0,<0.69.0"
RUN python -m pip install "uvicorn>=0.15.0,<0.16.0"
RUN python -m pip install "pandas>=1.1.5"
RUN python -m pip install scipy==1.8.0
RUN python -m pip install numpy==1.22.3
RUN python -m pip install pyshp==2.2.0
RUN python -m pip install scikit-learn==1.1.2
RUN python -m pip install Pillow==9.3.0
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
CMD ["uvicorn", "app.main:app", "--app-dir", "/usr/local/lib/python3.9/site-packages/spatialprofilingtoolbox/apiserver/", "--host", "0.0.0.0", "--port", "8080", "--log-level", "debug"]
