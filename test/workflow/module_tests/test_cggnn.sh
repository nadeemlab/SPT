spt workflow configure --local --workflow='cggnn' --study-name='Melanoma intralesional IL2' --database-config-file=../db/.spt_db.config.container --workflow-config-file=module_tests/.workflow.config
nextflow run .

# Check if the workflow ran successfully and if the expected output files exist
if [ $? -ne 0 ] || [ ! -e "results/model/model_best_validation_accuracy.pt" ] || [ ! -e "results/model/model_best_validation_loss.pt" ] || [ ! -e "results/model/model_best_validation_weighted_f1_score.pt" ] || [ ! -e "results/importances.csv" ] || [ ! -e "results/feature_names.txt" ] || [ ! -e "results/graphs.pkl" ]; then
    echo "Error during nextflow run or expected output files do not exist" >&2
    exit 1
fi

cat work/*/*/.command.log

# Check that the size of the output model is within 1% of the expected size
model_size=$(wc -c <"results/model/model_best_validation_accuracy.pt")
canon_model_size=1362921
if (( (100 * $model_size < $(( 99 * $canon_model_size ))) || (100 * $model_size > $(( 101 * $canon_model_size ))) ));
then
    echo "Output model is not within 1% of expected size ($canon_model_size): $model_size"
    exit 1
else
    echo "Output model size is within 1% of expected size."
fi

# Check if the length of the output importance file is as expected
importance_length=$(wc -l <"results/importances.csv")
canon_importance_length=149
if [[ $importance_length != $canon_importance_length ]];
then
    echo "Output importance file ($importance_length) is not the expected length ($canon_importance_length)."
    exit 1
else
    echo "Output importance scores file is the expected length $canon_importance_length."
fi

# Check if the approximate average of the importance scores is as expected
function approximate_average() {
    vals=$(cut -f2 -d, $1 | tail -n +2 | tr '\n' '+');
    vals=$(echo "$vals" | sed 's/\+$//g');
    echo "($vals)%"$(($(wc -l < $1 | sed 's/ //g') -1 )) | bc | head -c4
}
_average=$(approximate_average results/importances.csv)
expected_average=39
if [ ! $(echo "100*${_average} == $expected_average" | bc) == "0" ];
then
    echo "Expected approximate average .$expected_average , got ${_average} ."
    exit 1
else
    echo "Got expected approximate average .$expected_average ."
fi

# Check that at least half of the top 100 most important histological structures are the same as the reference
top_100_structures=$(tail -n +2 results/importances.csv | sort -t, -k2 -nr | awk -F, 'NR <= 100 {print $1}')
echo "$top_100_structures" > top_100_structures.txt
top_100_reference=$(tail -n +2 module_tests/reference_importance.csv | sort -t, -k2 -nr | awk -F, 'NR <= 100 {print $1}')
echo "$top_100_reference" > top_100_reference.txt
overlap=$(grep -Fxf top_100_reference.txt top_100_structures.txt)
overlap_count=$(echo "$overlap" | wc -l)
if [ $overlap_count -lt 50 ]; then
    echo "$overlap_count% of the most important histological structures match the reference, which is less than 50%" >&2
    exit 1
else
    echo "$overlap_count% of the most important histological structures match the reference."
fi

# Clean up
rm -f .nextflow.log*; rm -rf .nextflow/; rm -f configure.sh; rm -f run.sh; rm -f main.nf; rm -f nextflow.config; rm top_100_structures.txt; rm top_100_reference.txt; rm -rf results/
