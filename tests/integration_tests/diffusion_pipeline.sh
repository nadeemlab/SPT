#!/bin/bash

export DEBUG=1
cp integration_tests/example_config_files/diffusion.json .spt_pipeline.json
source test_run_pipeline.sh

odir=reference_outputs/diffusion
filename=diffusion_distance_tests.csv
cat output/$filename | sort > normalized1
cat $odir/$filename | sort > normalized2
if numpy-cmp normalized1 normalized2;
then
    exit 0
else
    exit 1
fi
