#!/bin/bash

spt-configure --local --input-path=./data_compartments_explicit --workflow='Multiplexed IF density'
nextflow run .
