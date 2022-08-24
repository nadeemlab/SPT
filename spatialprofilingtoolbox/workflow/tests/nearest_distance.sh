#!/bin/bash

spt-configure --local --input-path=./data --workflow='nearest distance to compartment'
nextflow run .
