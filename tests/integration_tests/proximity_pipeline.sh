#!/bin/bash

spt-configure --local --input-path=./data --workflow='phenotype proximity' --database-config-file=~/.spt_db.config.local
nextflow run .
