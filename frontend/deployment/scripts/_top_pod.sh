#!/bin/bash

while [[ true ]];
do
    usage=$(kubectl top pod)
    clear; echo "$usage"
    sleep 3
done
