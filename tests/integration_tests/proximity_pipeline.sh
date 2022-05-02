#!/bin/bash

spt-pipeline configure --local --input-path=./data --workflow='Multiplexed IF phenotype proximity'
nextflow run .
