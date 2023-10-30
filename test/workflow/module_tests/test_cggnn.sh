
spt workflow configure --local --workflow='cggnn' --study-name='Melanoma intralesional IL2' --database-config-file=../db/.spt_db.config.container --workflow-config-file=module_tests/.workflow.config
nextflow run .

$([ $? -eq 0 ] && [ -e "results/mi2_model.pt" ] && [ -e "results/mi2_importances.csv" ])
status="$?"

cat work/*/*/.command.log

model_size=$(wc -c <"results/mi2_model.pt")
canon_model_size=1362921
if (( (100 * $model_size < $(( 99 * $canon_model_size ))) || (100 * $model_size > $(( 101 * $canon_model_size ))) ));
then
    echo "Output model is not within 1% of expected size ($canon_model_size): $model_size"
    exit 1
else
    echo "Output model size is within 1% of expected size."
fi

importance_length=$(wc -l <"results/mi2_importances.csv")
canon_importance_length=180
if [[ $importance_length != $canon_importance_length ]];
then
    echo "Output importance file ($importance_length) is not the expected length ($canon_importance_length)."
    exit 1
else
    echo "Output importance scores file is the expected length $canon_importance_length."
fi

function approximate_average() {
    vals=$(cut -f2 -d, $1 | tail -n +2 | tr '\n' '+');
    vals=$(echo "$vals" | sed 's/\+$//g');
    echo "($vals)%"$(($(wc -l < $1 | sed 's/ //g') -1 )) | bc | head -c4
}

_average=$(approximate_average results/mi2_importances.csv)
expected_average=39

if [ ! $(echo "100*${_average} == $expected_average" | bc) == "0" ];
then
    echo "Expected approximate average .$expected_average , got ${_average} ."
    exit 1
else
    echo "Got expected approximate average .$expected_average ."
fi

rm -f .nextflow.log*; rm -rf .nextflow/; rm -f configure.sh; rm -f run.sh; rm -f main.nf; rm -f nextflow.config; rm -rf results/

if [ $? -gt 0 ] || [ $status -gt 0 ] ;
then
    echo "Error during nextflow run." >&2
    exit 1
else
    exit 0
fi
