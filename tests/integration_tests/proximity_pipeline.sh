#!/bin/bash

cp integration_tests/example_config_files/proximity.json .spt_pipeline.json
spt-pipeline configure
nextflow -c nextflow.config.local run spt_pipeline.nf
