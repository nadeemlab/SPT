#!/bin/bash

spt-configure --local --input-path=./data --workflow='Multiplexed IF density'
nextflow run .
