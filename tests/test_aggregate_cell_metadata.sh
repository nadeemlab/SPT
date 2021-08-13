#!/bin/bash

cp sample_config_file_proximity.txt .spt_pipeline.config
spt-aggregate-cell-data
spt-aggregate-cell-data --max-per-sample 5
spt-aggregate-cell-data --max-per-sample 10
spt-aggregate-cell-data --max-per-sample 57
rm .spt_pipeline.config
