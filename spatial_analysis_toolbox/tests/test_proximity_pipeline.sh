#!/bin/bash

cp sample_config_file_proximity.txt .sat_pipeline.config
sat-pipeline
rm .sat_pipeline.config
