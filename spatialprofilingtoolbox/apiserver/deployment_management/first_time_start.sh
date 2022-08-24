#!/bin/bash
imageid=$(sudo docker images --format="{{.Repository}} {{.ID}}" | grep 'pathstats-api-app' | grep -o '[a-z0-9]\+$')
sudo docker container run \
 -d \
 -p 8080:8080 \
 --name pathstats-app-api-instance \
 --env-file .spt_db.config.local \
 $imageid
