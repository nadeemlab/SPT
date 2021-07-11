#!/bin/bash
datestring=$(date +'%m-%d-%Y_%H-%M')
version=$(cat ../spatial_profiling_toolbox/spatial_profiling_toolbox/version.txt)
suffix="v$version""_""$datestring"
filename="spt_$suffix.sif"
sudo singularity build "$filename" singularity_container.def
