FROM ubuntu:22.04
RUN apt update && apt-get install -y apt-transport-https && apt-get clean
ARG DEBIAN_FRONTEND=noninteractive
RUN apt install software-properties-common -y && apt-get clean
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt update
RUN apt-get install -y libpq-dev && apt-get clean
RUN apt install openjdk-11-jdk -y && apt-get clean
RUN apt install xxd -y && apt-get clean
RUN apt install file -y && apt-get clean
WORKDIR /usr/src/app
ENV PATH="/usr/src/app:$PATH"
RUN apt install curl -y
RUN curl -s https://get.nextflow.io | bash; if [[ "$(which nextflow)" == "" ]]; then echo "nextflow not really installed."; exit 1; fi;
RUN apt install python3.11 -y && apt-get clean
RUN apt install python3.11-dev -y && apt-get clean
RUN apt install python3.11-venv -y && apt-get clean
RUN apt install python3.11-distutils && apt-get clean
ARG PIP_NO_CACHE_DIR=1
RUN ln -s /usr/bin/python3.11 /usr/bin/python
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python
RUN apt install gcc -y && apt-get clean
RUN apt install postgresql-client -y && apt-get clean
RUN apt-get install -y build-essential libssl-dev libffi-dev && apt-get clean
RUN apt-get install -y brotli && apt-get clean
RUN python -m pip install -U pip
COPY README.md .
COPY pyproject.toml.unversioned .
RUN python -m pip install toml
RUN apt install libgdal-dev -y && apt-get clean
RUN python -c 'import toml; c = toml.load("pyproject.toml.unversioned"); print("\n".join(c["project"]["dependencies"]))' | python -m pip install -r /dev/stdin
RUN python -c 'import toml; c = toml.load("pyproject.toml.unversioned"); print("\n".join(c["project"]["optional-dependencies"]["all"]))' | python -m pip install -r /dev/stdin
RUN python -m pip install build
RUN python -m pip install twine
RUN apt install -y bc && apt-get clean
RUN rm pyproject.toml.unversioned
CMD bash -c "echo 'available for commands'; while [ 0 -le 1 ]; do sleep 3600; echo 'sleep 3600... keep alive the container for availability for ongoing commands.'; done"
