#!/bin/bash

export DEBUG=1
rm -rf output/
cp example_config_files/front_proximity.txt .spt_pipeline.config
spt-pipeline
spt-analyze-results
rm .spt_pipeline.config
for script in schedule_*.sh;
do
    rm $script
done
