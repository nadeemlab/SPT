#!/bin/bash

if [[ "$1" == "version-updated" ]];
then
    FOUND_VERSION_CHANGE="no"
    status=$(git status -s |
    {
        while IFS= read -r line
        do
            is_modified_file=$(echo "$line" | grep -oE '^ ?M' | head -n1)
            if [[ "$is_modified_file" == ' M' || "$is_modified_file" == 'M' ]]; then
                if [[ "$line" == ' M spatialprofilingtoolbox/version.txt' ]]; then
                    FOUND_VERSION_CHANGE="yes"
                fi
            fi
        done
        echo -n $FOUND_VERSION_CHANGE
    })
fi

if [[ "$1" == "something-else-updated" ]];
then
    FOUND_ANOTHER_CHANGE='no'
    status=$(git status -s |
    {
        while IFS= read -r line
        do
            is_modified_file=$(echo "$line" | grep -oE '^ ?M' | head -n1)
            if [[ "$is_modified_file" == ' M' || "$is_modified_file" == 'M' ]]; then
                if [[ "$line" != ' M spatialprofilingtoolbox/version.txt' ]]; then
                    FOUND_ANOTHER_CHANGE="yes"
                fi
            fi

            is_added_file=$(echo "$line" | grep -oE '^A[M ] ' | head -n1)
            if [[ "$is_added_file" != "" ]]; then
                FOUND_ANOTHER_CHANGE="yes"
            fi
        done
        echo -n $FOUND_ANOTHER_CHANGE
    })
fi

echo $status
