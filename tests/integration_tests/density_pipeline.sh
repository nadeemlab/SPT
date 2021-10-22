#!/bin/bash

export DEBUG=1
cp integration_tests/example_config_files/density.json .spt_pipeline.json
source test_run_pipeline.sh
