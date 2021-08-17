#!/bin/bash

function _cleanup() {
    for file in .cell_metadata.tsv.cache .file_metadata.cache .fov_lookup.tsv.cache .pipeline.db ;
    do
        if [[ -f $file ]];
        then
            rm $file
        fi
    done
    for directory in jobs logs output __pycache__ ;
    do
        if [[ -d $directory ]];
        then
            rm -rf $directory
        fi
    done
    for tsv_file in cell_metadata_*.tsv;
    do
        if [[ -f $tsv_file ]];
        then
            rm $tsv_file
        fi
    done
}

set -e
source integration_tests/com.lehmannro.assert.sh/assert.sh

self_name=`basename "$0"`
source_note_color="\e[36;40m"
yellow="\e[33m"
reset="\e[0m"
back4="\e[4D"
blink="\e[5m"

for script in integration_tests/*.sh;
do
    if [[ -f $script ]];
    then
        echo -en "$source_note_color[$self_name]$reset $yellow$script $blink... $reset"
        assert_raises "$script" 0
        echo -e "$back4   "
        _cleanup
    fi
done

assert_end "SPT workflows integration"
