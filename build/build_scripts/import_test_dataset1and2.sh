
function nf_clean() {
    rm -rf work/
    rm -rf results/
    rm -rf .nextflow/
    rm -f .nextflow.config
    rm -f .nextflow.log
    rm -f .nextflow.log.*
    rm -f main.nf
}

spt workflow configure --local --input-path test/test_data/adi_preprocessed_tables/dataset1/ --workflow='HALO import' --database-config-file build/db/.spt_db.config.local
nextflow run .
cat work/*/*/.command.log

nf_clean

spt workflow configure --local --input-path test/test_data/adi_preprocessed_tables/dataset2/ --workflow='HALO import' --database-config-file build/db/.spt_db.config.local
nextflow run .
cat work/*/*/.command.log

nf_clean
