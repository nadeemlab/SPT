#!/bin/bash

./service_stop.sh && \
 ./service_drop.sh && \
 ./get_image.sh && \
 sudo docker image prune -f && \
 ./first_time_start.sh

