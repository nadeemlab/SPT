#!/bin/bash

export DEBUG=1
cp example_config_files/diffusion.txt .spt_pipeline.config
spt-analyze-results > logs/test_analysis_diffusion.out
