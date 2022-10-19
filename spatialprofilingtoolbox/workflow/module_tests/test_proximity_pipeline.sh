#!/bin/bash

spt workflow configure --local --input-path=../test_data/adi_preprocessed_tables/ --workflow='phenotype proximity' --database-config-file=../db/.spt_db.config.local
nextflow run .
