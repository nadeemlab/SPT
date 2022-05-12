#!/bin/bash

spt-configure --local --input-path=./data_no_compartments_no_outcomes/ --workflow='phenotype density'
nextflow run .
