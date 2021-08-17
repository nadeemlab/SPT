#!/bin/bash

export DEBUG=1
rm -rf output/
for script in schedule_*.sh;
do
    rm $script
done
cp example_config_files/proximity.txt .spt_pipeline.config
spt-pipeline
spt-analyze-results
rm .spt_pipeline.config
