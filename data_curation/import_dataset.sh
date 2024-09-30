#!/bin/bash

source convenience_scripts/verifications_and_configurations.sh
source convenience_scripts/import_functions.sh

dbconfigargument=$1
dbconfig=$(handle_dbconfig_argument $dbconfigargument)

drop_first=$( if [[ "$2" == "--drop-first" ]]; then echo "yes"; else echo "no" ; fi; )

one_inclusion="$3"

available_datasets=$(get_available_dataset_handles)
configured_datasets=$(get_configured_run_handles)
if [[ ! "$available_datasets" == "$configured_datasets" ]];
then
    bash convenience_scripts/configure_all_imports.sh "$dbconfigargument" "$one_inclusion"
    var=$?
    if [ $var -ne 0 ];
    then
        echo "Configuration had some error. $var"
        exit 1
    fi
fi

SECONDS=0
if [[ "$one_inclusion" == "" ]];
then
    configured_datasets=$(get_configured_run_handles)
else
    configured_datasets=$(get_configured_run_handles | grep -o "$one_inclusion")
fi
echo "Will import from configured run directories:"
echo "$configured_datasets" | sed 's/  /\n  /g'
echo "Command: import_datasets '$configured_datasets' $PWD $drop_first $dbconfig"
import_datasets "$configured_datasets" "$PWD" "$drop_first" "$dbconfig"
echo "Dataset import took $SECONDS seconds ("$(( SECONDS / 60 ))" minutes)."
