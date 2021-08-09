#!/bin/bash

export DEBUG=1
rm -rf output/
rm schedule_*
cp sample_config_file_frequency.txt .spt_pipeline.config
spt-pipeline
spt-analyze-results &> logs/integration.txt
rm .spt_pipeline.config
