#!/bin/bash

spt-configure --local --input-path=./data --workflow='HALO import'
nextflow run .
