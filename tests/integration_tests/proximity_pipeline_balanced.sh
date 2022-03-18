#!/bin/bash

cp integration_tests/example_config_files/proximity_balanced.json .spt_pipeline.json
spt-pipeline run
