#!/bin/bash

export DEBUG=1
rm -rf output/
for script in schedule_*.sh;
do
    rm $script
done
cp example_config_files/density.txt .spt_pipeline.config
spt-pipeline
spt-analyze-results &> logs/integration.txt
rm .spt_pipeline.config
