#!/bin/bash

export DEBUG=1
cp example_config_files/proximity.txt .spt_pipeline.config
spt-analyze-results > logs/test_analysis_proximity.out
