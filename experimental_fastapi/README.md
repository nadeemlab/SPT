
```
docker build -t fastapiimage .

docker run -d --name myfastapi -p 80:80 fastapiimage

docker container stop myfastapi
...
docker container start myfastapi
...
```