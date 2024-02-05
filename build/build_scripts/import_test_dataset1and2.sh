
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

cat build/build_scripts/.workflow.config | sed 's/YYY/1/g' > .workflow.config
spt workflow configure --workflow='tabular import' --config-file=.workflow.config
nextflow run .
cat work/*/*/.command.log

nf_clean

cat build/build_scripts/.workflow.config | sed 's/YYY/2/g' > .workflow.config
spt workflow configure --workflow='tabular import' --config-file=.workflow.config
nextflow run .
cat work/*/*/.command.log

nf_clean

echo "Running: spt ondemand cache-expressions-data-array"
spt ondemand cache-expressions-data-array --database-config-file build/db/.spt_db.config.local

spt db status --database-config-file build/db/.spt_db.config.local > counts.txt
cat counts.txt
diff counts.txt build/build_scripts/expected_counts_1and2.txt
status=$?
rm counts.txt
consider_exit $status
