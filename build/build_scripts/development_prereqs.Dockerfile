FROM ubuntu:22.04
RUN apt update
RUN apt install python3 python3-pip -y
RUN apt install python3-venv -y
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN apt-get install -y libpq-dev
RUN apt install curl -y
RUN apt install openjdk-11-jdk -y
RUN apt install xxd
WORKDIR /usr/src/app
ENV PATH="/usr/src/app:$PATH" 
RUN curl -s https://get.nextflow.io | bash
RUN apt install postgresql-client -y
COPY README.md .
COPY pyproject.toml.unversioned .
RUN python -m pip install toml
RUN python -c 'import toml; c = toml.load("pyproject.toml.unversioned"); print("\n".join(c["project"]["dependencies"]))' | python -m pip install -r /dev/stdin
RUN python -c 'import toml; c = toml.load("pyproject.toml.unversioned"); print("\n".join(c["project"]["optional-dependencies"]["all"]))' | python -m pip install -r /dev/stdin
RUN python -m pip install build
RUN python -m pip install twine
CMD bash -c "echo 'available for commands'; while [ 0 -le 1 ]; do sleep 3600; echo 'sleep 3600... keep alive the container for availability for ongoing commands.'; done"