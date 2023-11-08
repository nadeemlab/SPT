FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /usr/src/app
RUN apt install -y libgdal-dev
RUN python -m pip install psycopg2==2.9.6
RUN python -m pip install adiscstudies==0.11.0
RUN python -m pip install numba==0.57.0
RUN python -m pip install attrs==23.1.0
RUN python -m pip install pandas==2.0.2
RUN python -m pip install numpy==1.24.3
RUN python -m pip install scikit-learn==1.2.2
RUN python -m pip install pyshp==2.2.0
RUN python -m pip install pydantic==2.0.2
RUN python -m pip install squidpy==1.3.0
ARG version
ARG service_name
ARG WHEEL_FILENAME
LABEL version=$version
LABEL service_name=$service_name
ENV service_name $service_name
COPY $WHEEL_FILENAME ./
RUN python -m pip install "$WHEEL_FILENAME"
ENV API_SERVER_PORT=8016
ENTRYPOINT ["spt", "ondemand", "start", "--host", "0.0.0.0", "--port", "8016", "--timeout-seconds", "120"]
