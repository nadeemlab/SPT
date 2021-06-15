#!/bin/bash

export DEBUG=1
rm -rf output/
rm schedule_*
cp sample_config_file_diffusion.txt .sat_pipeline.config
sat-pipeline
rm .sat_pipeline.config
