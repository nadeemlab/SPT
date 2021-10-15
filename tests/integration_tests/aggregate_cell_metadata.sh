#!/bin/bash

cp integration_tests/example_config_files/proximity.json .spt_pipeline.json
spt-aggregate-cell-data
spt-aggregate-cell-data --max-per-sample 5
spt-aggregate-cell-data --max-per-sample 10
spt-aggregate-cell-data --max-per-sample 57
rm .spt_pipeline.json
