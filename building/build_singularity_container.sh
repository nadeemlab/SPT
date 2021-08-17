#!/bin/bash
datestring=$(date +'%m-%d-%Y_%H-%M')
version=$(cat ../spatialprofilingtoolbox/version.txt)
suffix="v$version""_""$datestring"
filename="spt_$suffix.sif"
sudo singularity build "$filename" singularity_container.def
if test -f "$filename";
then
    exit 0
else
    exit 1
fi
