#!/bin/bash

spt-configure --local --input-path=./data --workflow='Multiplexed IF phenotype proximity'
nextflow run .
