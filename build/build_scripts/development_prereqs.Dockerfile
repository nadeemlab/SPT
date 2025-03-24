FROM ubuntu:24.04
ARG DEBIAN_FRONTEND=noninteractive
RUN apt update && apt-get install -y apt-transport-https && apt-get clean
RUN apt install software-properties-common -y && apt-get clean
RUN apt-get install -y libpq-dev && apt-get clean
RUN apt install openjdk-11-jdk -y && apt-get clean
RUN apt install xxd -y && apt-get clean
RUN apt install file -y && apt-get clean
RUN apt install -y bc && apt-get clean
RUN apt install gcc -y && apt-get clean
RUN apt install postgresql-client -y && apt-get clean
RUN apt-get install -y build-essential libssl-dev libffi-dev && apt-get clean
RUN apt-get install -y brotli && apt-get clean
RUN apt install curl -y
RUN curl -s https://get.nextflow.io | bash; mv nextflow /usr/local/bin/;
RUN bash -c 'if [[ "$(which nextflow)" = "" ]]; then echo "Nextflow not on path."; exit 1; fi;'
RUN apt install libgdal-dev -y && apt-get clean
RUN add-apt-repository ppa:deadsnakes/ppa && apt update
RUN apt install python3.13 -y && apt-get clean
RUN apt install python3.13-dev -y && apt-get clean
RUN apt install python3.13-venv -y && apt-get clean
ENV VIRTUAL_ENV=/opt/venv
RUN python3.13 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ARG PIP_NO_CACHE_DIR=1
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python
RUN python -m pip install -U pip
COPY requirements.txt .
RUN grep setuptools requirements.txt | xargs python -m pip install
RUN python -m pip install -r requirements.txt --no-build-isolation
RUN python -m pip install build
RUN python -m pip install twine
COPY README.md .
CMD bash -c "echo 'available for commands'; while [ 0 -le 1 ]; do sleep 3600; echo 'sleep 3600... keep alive the container for availability for ongoing commands.'; done"
