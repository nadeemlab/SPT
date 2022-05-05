#!/bin/bash

spt-configure --local --input-path=./data --workflow='phenotype proximity'
nextflow run .
