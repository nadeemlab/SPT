#!/bin/bash

export DEBUG=1
cp integration_tests/example_config_files/density_with_thresholding.json .spt_pipeline.json
source test_run_pipeline.sh
