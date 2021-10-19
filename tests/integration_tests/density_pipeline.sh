#!/bin/bash

export DEBUG=1
cp integration_tests/example_config_files/density.json .spt_pipeline.json
source test_run_pipeline.sh

check_output_file_sum aa71d781126f4b889b14e6634858ca6c72944663567a62a6f91b0b36682cd0aa output/density_tests.csv
