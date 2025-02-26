FROM postgres:17.2
WORKDIR /usr/src/app
ENV DEBIAN_FRONTEND=noninteractive
ARG PIP_NO_CACHE_DIR=1
RUN apt update && apt-get clean
RUN apt install -y libpq-dev && apt-get clean
RUN localedef -i en_US -f UTF-8 en_US.UTF-8
CMD ["postgres", "-h", "0.0.0.0"]
