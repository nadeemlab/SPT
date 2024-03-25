#!/bin/bash

currenthost=$(cat currenthost.txt)
cd ../application/
docker build -t spt-frontend-prod-build -f ../deployment/build.Dockerfile .
mkdir -p dist
docker run \
    --mount type=bind,source="$(pwd)"/dist,target=/code/app/dist \
    -e VITE_API_URL="$currenthost" \
    spt-frontend-prod-build
cd ../
docker build -t nadeemlab-development/frontend -t spt-frontend-prod -f ./deployment/Dockerfile .
