#!/bin/bash

cp integration_tests/example_config_files/density_with_thresholding.json .spt_pipeline.json
spt-pipeline run
