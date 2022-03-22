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

    if [[ -f normalized1 ]];
    then
        rm normalized1
    fi
    if [[ -f normalized2 ]];
    then
        rm normalized2
    fi

    if [[ -f 'example_merged.db' ]];
    then
        rm 'example_merged.db'
    fi
}

function _test_cleanup() {
    rm -rf work/
    rm -rf .nextflow/
}