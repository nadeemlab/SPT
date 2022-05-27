#!/bin/bash

spt-configure --local --input-path=./data --workflow='HALO import' --database-config-file='.spt_db.config.local'
nextflow run .
