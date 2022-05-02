#!/bin/bash

spt-configure --local --input-path=./data --workflow='Multiplexed IF density proximity' # --use-intensities ??
nextflow run .
