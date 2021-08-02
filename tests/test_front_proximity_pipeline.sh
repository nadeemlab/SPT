#!/bin/bash

export DEBUG=1
rm -rf output/
rm schedule_*
cp sample_config_file_front_proximity.txt .spt_pipeline.config
spt-pipeline
spt-analyze-results
rm .spt_pipeline.config
