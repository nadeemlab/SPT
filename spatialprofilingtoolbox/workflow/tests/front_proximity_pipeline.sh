#!/bin/bash

spt workflow configure --local --input-path=./data --workflow='front proximity'
nextflow run .
