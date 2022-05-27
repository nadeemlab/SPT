
```
docker build -t pathstatsapiappimage .
docker container stop pathstatsapiapp
docker container rm pathstatsapiapp
docker run -d --name pathstatsapiapp --env-file .spt_db.config.env -p 80:80 pathstatsapiappimage

docker container stop pathstatsapiapp
docker container start pathstatsapiapp

```