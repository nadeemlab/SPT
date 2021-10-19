#!/bin/bash

export DEBUG=1
cp integration_tests/example_config_files/diffusion.json .spt_pipeline.json
source test_run_pipeline.sh

cat output/diffusion_distance_tests.csv | sort > output/diffusion_distance_tests.csv.normalized
check_output_file_sum c9c02c8f84a8dae34cdbcc2293fa60215714222ae59ddd7f4daae023347e4b57 output/diffusion_distance_tests.csv.normalized
rm output/diffusion_distance_tests.csv.normalized
