#!/bin/bash

repository_url=666466118732.dkr.ecr.us-east-1.amazonaws.com

function check_aws_logged_in() {
    aws sts get-caller-identity 1>/dev/null 2>/dev/null
    if [[ "$?" != "0" ]];
    then
        echo "This session does not have AWS credentials set up."
        exit 1
    else
        echo "AWS credentials found in session environment."
    fi
}

function login_stuff() {
    check_aws_logged_in
    bash scripts/start_docker_daemon.sh
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "$repository_url"
}

function push_frontend_image() {
    docker tag spt-frontend-prod $repository_url/spt-frontend-prod:latest
    docker push "$repository_url/spt-frontend-prod:latest"
}

login_stuff
push_frontend_image
