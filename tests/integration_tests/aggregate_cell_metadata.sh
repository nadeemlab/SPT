#!/bin/bash

cp integration_tests/example_config_files/proximity.txt .spt_pipeline.config
spt-aggregate-cell-data
spt-aggregate-cell-data --max-per-sample 5
spt-aggregate-cell-data --max-per-sample 10
spt-aggregate-cell-data --max-per-sample 57
rm .spt_pipeline.config
