#!/bin/bash

cp integration_tests/example_config_files/density.json .spt_pipeline.json
spt-pipeline run
