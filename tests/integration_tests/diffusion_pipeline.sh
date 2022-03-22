#!/bin/bash

cp integration_tests/example_config_files/diffusion.json .spt_pipeline.json
spt-pipeline run
