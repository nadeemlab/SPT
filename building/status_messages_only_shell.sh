#!/bin/bash

if [[ "$2" == "-super-verbose" ]];
then
    shift
    shift
    exec /bin/bash -c "$@"
elif [[ "$2" == "-not-super-verbose" ]];
then
    shift
    shift
    echo "$@" | grep -qz 'make SHELL=' >/dev/null 2>&1
    found_make_shell="$?"
    if [[ ("$@" == *'verbose_command_wrapper.sh'*) || ("$found_make_shell" == "0") ]];
    then
        exec /bin/bash -c "$@"
    else
        exec /bin/bash -c "$@" >/dev/null 2>&1
    fi
else
    exec /bin/bash "$@"
fi
