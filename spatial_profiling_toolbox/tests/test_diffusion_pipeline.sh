#!/bin/bash

export DEBUG=1
rm -rf output/
rm schedule_*
cp sample_config_file_diffusion.txt .spt_pipeline.config
spt-pipeline
rm .spt_pipeline.config
