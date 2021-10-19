#!/bin/bash

export DEBUG=1
cp integration_tests/example_config_files/density_with_intensities.json .spt_pipeline.json
source test_run_pipeline.sh

cat output/density_tests.csv | sort > output/density_tests.csv.normalized
check_output_file_sum 3d3c99ce6bed46aff5450991123bfa8ab04be977b1a8ff24b5c96f17f5dc133b output/density_tests.csv.normalized
rm output/density_tests.csv.normalized
