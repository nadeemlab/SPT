#!/bin/bash

source cleaning.sh

set -e
source integration_tests/com.lehmannro.assert/assert.sh

self_name=`basename "$0"`
source_note_color="\033[36;40m"
yellow="\033[33m"
reset="\033[0m"
back4="\033[4D"
blink="\033[5m"

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
