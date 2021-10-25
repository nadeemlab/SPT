#!/bin/bash

export DEBUG=1
cp integration_tests/example_config_files/proximity.json .spt_pipeline.json
sed -i 's/"local"/"nextflow"/g' .spt_pipeline.json 
spt-pipeline generate-jobs
rm .spt_pipeline.json
