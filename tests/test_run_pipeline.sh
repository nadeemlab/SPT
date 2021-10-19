#!/bin/bash

check_output_file_sum() {
    expected=$1
    file=$2
    sum=$(sha256sum $file | grep -o "^$expected")
    if [ "$expected" != "$sum" ];
    then
        echo "SHA256 sum is wrong on file $file ."
        exit 1
    else
        echo "SHA256 sum checked out for file $file ."
    fi
}

spt-generate-jobs
for script in schedule_*.sh;
do
    chmod +x $script
    ./$script
done
spt-analyze-results &> logs/integration.txt
rm .spt_pipeline.json
for script in schedule_*.sh;
do
    rm $script
done
