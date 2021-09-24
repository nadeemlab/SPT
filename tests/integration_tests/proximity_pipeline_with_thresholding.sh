#!/bin/bash

export DEBUG=1
rm -rf output/
cp integration_tests/example_config_files/proximity_with_thresholding.txt .spt_pipeline.config
spt-pipeline
spt-analyze-results &> logs/integration.txt
rm .spt_pipeline.config
for script in schedule_*.sh;
do
    rm $script
done
