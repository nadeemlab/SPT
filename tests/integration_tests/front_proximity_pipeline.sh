#!/bin/bash

spt-configure --local --input-path=./data --workflow='Multiplexed IF front proximity'
nextflow run .
