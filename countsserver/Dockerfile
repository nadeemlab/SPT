FROM python:3.9-slim
WORKDIR /countsserver

COPY ./requirements.txt /countsserver/requirements.txt

RUN pip3 install --no-cache-dir --upgrade -r /countsserver/requirements.txt

COPY ./spt-counts-server /countsserver/
COPY ./log_formats.py /countsserver/
CMD ["spt-counts-server"]
