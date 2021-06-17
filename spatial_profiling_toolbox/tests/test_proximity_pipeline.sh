#!/bin/bash

export DEBUG=1
rm -rf output/
rm schedule_*
cp sample_config_file_proximity.txt .spt_pipeline.config
sat-pipeline
rm .spt_pipeline.config
