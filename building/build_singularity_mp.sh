#!/bin/bash

function abspath {
    if [[ -d "$1" ]]
    then
        pushd "$1" >/dev/null
        pwd
        popd >/dev/null
    elif [[ -e "$1" ]]
    then
        pushd "$(dirname "$1")" >/dev/null
        echo "$(pwd)/$(basename "$1")"
        popd >/dev/null
    else
        echo "$1" does not exist! >&2
        return 127
    fi
}

datestring=$(date +'%m-%d-%Y_%H-%M')
version=$(cat ../spatialprofilingtoolbox/version.txt)
suffix="v$version""_""$datestring"
filename="spt_$suffix.sif"

TMPDIR=/singularity
RECIPEPATH=$(abspath singularity_container.def)
SIFPATH="$filename"
dzdo singularity build --tmpdir=${TMPDIR} ${SIFPATH} ${RECIPEPATH}
