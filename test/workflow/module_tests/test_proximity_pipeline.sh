
spt workflow configure --local --workflow='phenotype proximity' --study-name='Melanoma intralesional IL2' --database-config-file=../db/.spt_db.config.container
nextflow run .

status=$?

cat work/*/*/.command.log

rm -f .nextflow.log*; rm -rf .nextflow/; rm -f configure.sh; rm -f run.sh; rm -f main.nf; rm -f nextflow.config; rm -rf work/; rm -rf results/

if [ $? -gt 0 ] ;
then
    echo "Error during nextflow run." >&2
    exit 1
fi

spt db status --database-config-file=../db/.spt_db.config.container > current_status.txt
echo "Left is computed, right is expected."
diff current_status.txt module_tests/expected_proximity_record_counts.txt
status=$?
rm current_status.txt

python module_tests/check_proximity_metric_values.py ../db/.spt_db.config.container

exit $status
