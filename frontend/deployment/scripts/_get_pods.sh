#!/bin/bash

while [[ true ]];
do
    usage=$(kubectl get pods -o wide)
    clear; echo "$usage"
    sleep 3
done
