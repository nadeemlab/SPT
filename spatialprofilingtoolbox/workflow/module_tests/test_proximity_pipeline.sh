#!/bin/bash

spt workflow configure --local --input-path=../test_data/adi_preprocessed_tables/ --workflow='phenotype proximity' --database-config-file=../db/.spt_db.config.local
nextflow run .

status=$?
rm -f .nextflow.log*; rm -rf .nextflow/; rm -f configure.sh; rm -f run.sh; rm -f main.nf; rm -f nextflow.config; rm -rf work/; rm -rf results/

if [ $? -gt 0 ] ;
then
    echo "Error during nextflow run." >&2
    exit 1
fi

spt db status --database-config-file=../db/.spt_db.config.local > current_status.txt
diff current_status.txt module_tests/expected_proximity_record_counts.txt
status=$?
rm current_status.txt

exit $status