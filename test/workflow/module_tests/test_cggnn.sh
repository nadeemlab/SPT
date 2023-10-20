
spt workflow configure --local --workflow='cggnn' --study-name='Melanoma intralesional IL2' --database-config-file=../db/.spt_db.config.container --workflow-config-file=module_tests/.workflow.config
cat nextflow.config
nextflow run .

status=$?

$([ $? -eq 0 ] && [ -e "results/mi2_model.pt" ] && [ -e "results/mi2_importances.csv" ])
status="$?"

head "results/mi2_importances.csv"

rm -f .nextflow.log*; rm -rf .nextflow/; rm -f configure.sh; rm -f run.sh; rm -f main.nf; rm -f nextflow.config; rm -rf results/

if [ $? -gt 0 ] || [ $status -gt 0 ] ;
then
    echo "Error during nextflow run." >&2
    exit 1
else
    exit 0
fi
