#!/bin/bash

spt-pipeline configure --local --input-path=./data --workflow='Multiplexed IF density'
nextflow run .
