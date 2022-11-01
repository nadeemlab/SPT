
function consider_exit() {
    if [[ "$1" != "0" ]];
    then
        exit 1
    fi
}

spt db create-schema --database-config-file .spt_db.config.container --force
spt workflow configure --local --input-path ../test_data/adi_preprocessed_tables/dataset1/ --workflow='HALO import' --database-config-file .spt_db.config.container; nextflow run .
spt db status --database-config-file .spt_db.config.container > counts.txt; diff counts.txt module_tests/record_counts1.txt
status=$?
rm counts.txt
[ $status -eq 0 ] && echo "Dataset 1 import created correct number of records." || echo "Import of dataset 1 failed."
consider_exit $status

spt db create-schema --database-config-file .spt_db.config.container --force
spt workflow configure --local --input-path ../test_data/adi_preprocessed_tables/dataset2/ --workflow='HALO import' --database-config-file .spt_db.config.container; nextflow run .
spt db status --database-config-file .spt_db.config.container > counts.txt; diff counts.txt module_tests/record_counts2.txt
status=$?
rm counts.txt
[ $status -eq 0 ] && echo "Dataset 2 import created correct number of records." || echo "Import of dataset 2 failed."
consider_exit $status

spt db create-schema --database-config-file .spt_db.config.container --force
spt workflow configure --local --input-path ../test_data/adi_preprocessed_tables/dataset1/ --workflow='HALO import' --database-config-file .spt_db.config.container; nextflow run .
spt workflow configure --local --input-path ../test_data/adi_preprocessed_tables/dataset2/ --workflow='HALO import' --database-config-file .spt_db.config.container; nextflow run .
spt db status --database-config-file .spt_db.config.container > counts.txt; diff counts.txt module_tests/record_counts_1_2.txt
status=$?
rm counts.txt
[ $status -eq 0 ] && echo "Dataset 1 and 2 import created correct combined number of records." || echo "Combined import of datasets 1 and 2 failed."
consider_exit $status

spt db create-schema --database-config-file .spt_db.config.container --force
spt workflow configure --local --input-path ../test_data/adi_preprocessed_tables/dataset2/ --workflow='HALO import' --database-config-file .spt_db.config.container; nextflow run .
spt workflow configure --local --input-path ../test_data/adi_preprocessed_tables/dataset1/ --workflow='HALO import' --database-config-file .spt_db.config.container; nextflow run .
spt db status --database-config-file .spt_db.config.container > counts.txt; diff counts.txt module_tests/record_counts_1_2.txt
status=$?
rm counts.txt
[ $status -eq 0 ] && echo "Dataset 2 *then* 1 import created correct combined number of records." || echo "Combined import of datasets 2 *then* 1 failed."
consider_exit $status
