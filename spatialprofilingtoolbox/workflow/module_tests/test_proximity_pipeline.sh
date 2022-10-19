#!/bin/bash

spt workflow configure --local --input-path=../test_data/adi_preprocessed_tables/ --workflow='phenotype proximity' --database-config-file=../db/.spt_db.config.local
nextflow run .
rm -f .nextflow.log*; rm -rf .nextflow/; rm -f configure.sh; rm -f run.sh; rm -f main.nf; rm -f nextflow.config; rm -rf work/; rm -rf results/

spt db status --database-config-file=../db/.spt_db.config.local
