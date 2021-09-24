#!/bin/bash

export DEBUG=1
rm -rf output/
cp integration_tests/example_config_files/front_proximity.txt .spt_pipeline.config
spt-pipeline
spt-analyze-results &> logs/integration.txt
rm .spt_pipeline.config
for script in schedule_*.sh;
do
    rm $script
done
