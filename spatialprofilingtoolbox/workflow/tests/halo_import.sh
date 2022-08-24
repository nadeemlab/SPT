#!/bin/bash

spt-configure --local --input-path=./data_subspecimens --workflow='HALO import' --database-config-file=~/.spt_db.config.local
nextflow run .
