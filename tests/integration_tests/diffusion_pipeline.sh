#!/bin/bash

export DEBUG=1
cp integration_tests/example_config_files/diffusion.json .spt_pipeline.json
source test_run_pipeline.sh

cat output/diffusion_distance_tests.csv | sort > output/diffusion_distance_tests.csv.normalized
check_output_file_sum da3738229fb8332de4a061a8e30eff1b31930443cd0526f791019d6f08de331d output/diffusion_distance_tests.csv.normalized
rm output/diffusion_distance_tests.csv.normalized
