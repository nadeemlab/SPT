#!/bin/bash

export DEBUG=1
cp sample_config_file_proximity.txt .sat_pipeline.config
sat-analyze-results > logs/test_analysis_proximity.out 2>&1 &
tail -f logs/test_analysis_proximity.out
