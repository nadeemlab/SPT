#!/bin/bash

function is_gnu_sed(){
    sed --version >/dev/null 2>&1
}

function sed_i_wrapper(){
    if is_gnu_sed; then
        $(which sed) "$@"
    else
        a=()
    for b in "$@";
    do
        [[ $b == '-i' ]] && a=("${a[@]}" "$b" "") || a=("${a[@]}" "$b")
    done
        $(which sed) "${a[@]}"
    fi
}
