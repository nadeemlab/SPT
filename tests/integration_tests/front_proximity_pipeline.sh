#!/bin/bash

spt-pipeline configure --local --input-path=./data --workflow='Multiplexed IF front proximity'
nextflow run .
