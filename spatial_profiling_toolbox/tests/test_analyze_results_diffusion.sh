#!/bin/bash

export DEBUG=1
cp sample_config_file_diffusion.txt .spt_pipeline.config
sat-analyze-results > logs/test_analysis_diffusion.out 2>&1 &
tail -f logs/test_analysis_diffusion.out
