#!/bin/bash

export DEBUG=1
rm -rf output/
cp integration_tests/example_config_files/front_proximity.json .spt_pipeline.json
spt-pipeline
spt-analyze-results &> logs/integration.txt
rm .spt_pipeline.json
for script in schedule_*.sh;
do
    rm $script
done
