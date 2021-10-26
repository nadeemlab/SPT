#!/bin/bash

cp integration_tests/example_config_files/proximity.json .spt_pipeline.json
spt-pipeline generate-jobs
rm .spt_pipeline.json
