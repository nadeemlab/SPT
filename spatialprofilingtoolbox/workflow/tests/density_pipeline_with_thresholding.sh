#!/bin/bash

spt-configure --local --input-path=./data --workflow='phenotype density'  # --dichotomize ??
nextflow run .
