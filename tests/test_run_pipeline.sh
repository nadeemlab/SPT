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

spt-pipeline generate-jobs
for script in schedule_*.sh;
do
    chmod +x $script
    ./$script
done
spt-pipeline aggregate-results &> logs/integration.txt
rm .spt_pipeline.json
for script in schedule_*.sh;
do
    rm $script
done

numpy-cmp() {
    f1=$1
    f2=$2
    cat $f1 | sed 's/\(\.[0-9]\{7\}\)\([0-9]\+\),/\1,/g' > abbreviated1
    cat $f2 | sed 's/\(\.[0-9]\{7\}\)\([0-9]\+\),/\1,/g' > abbreviated2
    if cmp -s abbreviated1 abbreviated2;
    then
        rm abbreviated1 abbreviated2
        return 0
    else
        rm abbreviated1 abbreviated2
        return 1
    fi
}
