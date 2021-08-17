#!/bin/bash

export DEBUG=1
rm -rf output/
for script in schedule_*.sh;
do
    rm $script
done
cp sample_config_file_density.txt .spt_pipeline.config
spt-pipeline
spt-analyze-results &> logs/integration.txt
rm .spt_pipeline.config
