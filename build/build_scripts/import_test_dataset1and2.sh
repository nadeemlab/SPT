
function nf_clean() {
    rm -rf work/
    rm -rf results/
    rm -rf .nextflow/
    rm -f .nextflow.config
    rm -f .nextflow.log
    rm -f .nextflow.log.*
    rm -f main.nf
}

function consider_exit() {
    if [[ "$1" != "0" ]];
    then
        exit 1
    fi
}

spt db create-schema --database-config-file=build/db/.spt_db.config.local

spt workflow configure --local --input-path test/test_data/adi_preprocessed_tables/dataset1/ --workflow='tabular import' --database-config-file build/db/.spt_db.config.local
nextflow run .
cat work/*/*/.command.log

nf_clean

spt workflow configure --local --input-path test/test_data/adi_preprocessed_tables/dataset2/ --workflow='tabular import' --database-config-file build/db/.spt_db.config.local
nextflow run .
cat work/*/*/.command.log

nf_clean

spt db create-schema --refresh-views-only --database-config-file build/db/.spt_db.config.local
spt db status --database-config-file build/db/.spt_db.config.local > counts.txt
cat counts.txt
diff counts.txt build/build_scripts/expected_counts_1and2.txt
status=$?
rm counts.txt
consider_exit $status
