#!/bin/bash

spt workflow configure --local --input-path=./data_subspecimens --workflow='HALO import' --database-config-file=~/.spt_db.config.local
nextflow run .

spt workflow configure --local --input-path=./data_subspecimens --workflow='phenotype proximity' --database-config-file=~/.spt_db.config.local
nextflow run .
