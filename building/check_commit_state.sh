#!/bin/bash
status=$(git status -s |
{
    FOUND_CHANGE='no'
    while IFS= read -r line
    do
        is_modified_file=$(echo "$line" | grep -oE '^ ?M' | head -n1)
        if [[ "$is_modified_file" == ' M' || "$is_modified_file" == 'M' ]];
            then
            FOUND_CHANGE="yes"
        fi

        is_added_file=$(echo "$line" | grep -oE '^A[M ] ' | head -n1)
        if [[ "$is_added_file" != "" ]]; then
            FOUND_CHANGE="yes"
        fi
    done
    echo -n $FOUND_CHANGE
})
echo $status
