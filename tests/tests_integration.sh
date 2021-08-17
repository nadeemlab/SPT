#!/bin/bash
set -e
source com.lehmannro.assert.sh/assert.sh

self_name=`basename "$0"`
source_note_color="\e[36;40m"
yellow="\e[33m"
reset="\e[0m"
back4="\e[4D"

for script in integration_tests/*.sh;
do
    echo -en "$source_note_color[$self_name]$reset $yellow$script ... $reset"
    assert_raises "$script" 0
    echo -e "$back4   "
done

assert_end "SPT workflows integration"

function _cleanup() {
    rm .cell_metadata.tsv.cache
    rm .file_metadata.cache
    rm .fov_lookup.tsv.cache
    rm .pipeline.db
    rm -rf jobs
    rm -rf logs
    rm -rf output
    rm cell_metadata_*.tsv
}
_cleanup
