#!/bin/bash
suffix=$(date +'%m-%d-%Y_%H-%M')
sudo singularity build "spt_$suffix.sif" singularity_container.def
