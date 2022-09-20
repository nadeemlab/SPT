
docker build -f ./Dockerfile -t testingavahi:latest .
docker run -i -t testingavahi


...

avahi-browse -a -r -t
