#!/bin/bash

FM=../test_data/adi_preprocessed_tables/dataset1/file_manifest.tsv
cp $FM file_manifest.tsv.bak
(cat file_manifest.tsv.bak | grep -vE '(0_2|0_3|6_2|6_3|6_4)') > $FM

spt workflow configure --local --workflow='phenotype proximity' --study-name='Melanoma intralesional IL2' --database-config-file=../db/.spt_db.config.container
nextflow run .

cp file_manifest.tsv.bak $FM
rm file_manifest.tsv.bak

status=$?
rm -f .nextflow.log*; rm -rf .nextflow/; rm -f configure.sh; rm -f run.sh; rm -f main.nf; rm -f nextflow.config; rm -rf work/; rm -rf results/

if [ $? -gt 0 ] ;
then
    echo "Error during nextflow run." >&2
    exit 1
fi

spt db status --database-config-file=../db/.spt_db.config.container > current_status.txt
diff current_status.txt module_tests/expected_proximity_record_counts.txt
status=$?
rm current_status.txt

exit $status
