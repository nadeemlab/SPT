FROM ubuntu:22.04
RUN apt update && apt-get install -y apt-transport-https
ARG DEBIAN_FRONTEND=noninteractive
RUN apt install software-properties-common -y
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt update
RUN apt-get install -y libpq-dev
RUN apt install openjdk-11-jdk -y
RUN apt install xxd -y
RUN apt install file -y
WORKDIR /usr/src/app
ENV PATH="/usr/src/app:$PATH"
RUN apt install curl -y
RUN curl -s https://get.nextflow.io | bash; if [[ "$(which nextflow)" == "" ]]; then echo "nextflow not really installed."; exit 1; fi;
RUN apt install python3.11 -y
RUN apt install python3.11-dev -y
RUN apt install python3.11-venv -y
RUN apt install python3.11-distutils
RUN ln -s /usr/bin/python3.11 /usr/bin/python
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python
RUN apt install gcc -y
RUN apt install postgresql-client -y
RUN apt-get install -y build-essential libssl-dev libffi-dev
RUN python -m pip install -U pip
COPY README.md .
COPY pyproject.toml.unversioned .
RUN python -m pip install toml
RUN python -c 'import toml; c = toml.load("pyproject.toml.unversioned"); print("\n".join(c["project"]["dependencies"]))' | python -m pip install -r /dev/stdin
RUN python -c 'import toml; c = toml.load("pyproject.toml.unversioned"); print("\n".join(c["project"]["optional-dependencies"]["all"]))' | python -m pip install -r /dev/stdin
RUN python -m pip install dgl -f https://data.dgl.ai/wheels/repo.html
ENV DGLBACKEND=pytorch
RUN python -m pip install build
RUN python -m pip install twine
RUN python -m pip install torch
RUN python -m pip install dgl -f https://data.dgl.ai/wheels/repo.html
ENV DGLBACKEND=pytorch
RUN apt install -y bc
CMD bash -c "echo 'available for commands'; while [ 0 -le 1 ]; do sleep 3600; echo 'sleep 3600... keep alive the container for availability for ongoing commands.'; done"
