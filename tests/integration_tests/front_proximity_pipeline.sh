#!/bin/bash

spt-configure --local --input-path=./data --workflow='front proximity'
nextflow run .
