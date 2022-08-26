#!/bin/bash

spt workflow configure --local --input-path=./data --workflow='phenotype density'
nextflow run .
