# Starts in build, needs to run in test
cd ../../test/workflow/

docker_image="$1"

function check_for_successful_run_with_outputs() {
    h5_files_count=$(ls results/*.h5 2> /dev/null | wc -l)
    if [ $? -ne 0 ] || \
       [ ! -e "results/model/model_best_validation_accuracy.pt" ] || \
       [ ! -e "results/model/model_best_validation_loss.pt" ] || \
       [ ! -e "results/model/model_best_validation_weighted_f1_score.pt" ] || \
       [ ! -e "results/importances.csv" ] || \
       [ ! -e "results/feature_names.txt" ] || \
       [ $h5_files_count -ne 4 ];
    then
        echo "Error during nextflow run or expected output files do not exist" >&2
        exit 1
    fi
}

function check_output_model_size() {
    model_size=$(wc -c <"results/model/model_best_validation_accuracy.pt")
    canon_model_size=1362921
    if (( (100 * $model_size < $(( 99 * $canon_model_size ))) || (100 * $model_size > $(( 101 * $canon_model_size ))) ));
    then
        echo "Output model is not within 1% of expected size ($canon_model_size): $model_size"
        exit 1
    else
        echo "Output model size is within 1% of expected size."
    fi
}

function check_importances_size() {
    importance_length=$(wc -l <"results/importances.csv" | sed 's/ //g')
    canon_importance_length=149
    if [[ $importance_length != $canon_importance_length ]];
    then
        echo "Output importance file ($importance_length) is not the expected length ($canon_importance_length)."
        exit 1
    else
        echo "Output importance scores file is the expected length $canon_importance_length."
    fi
}

function approximate_average() {
    vals=$(cut -f2 -d, $1 | tail -n +2 | tr '\n' '+');
    vals=$(echo "$vals" | sed 's/\+$//g');
    echo "($vals)%"$(($(wc -l < $1 | sed 's/ //g') -1 )) | bc | head -c4
}

function check_importance_scores_average() {
    _average=$(approximate_average results/importances.csv)
    expected_average=39
    if [ ! $(echo "100*${_average} == $expected_average" | bc) == "0" ];
    then
        echo "Expected approximate average .$expected_average , got ${_average} ."
        exit 1
    else
        echo "Got expected approximate average .$expected_average ."
    fi
}

function check_importance_cells_overlap() {
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
}

function clean() {
    rm -f .nextflow.log*
    rm -rf .nextflow/
    rm -f configure.sh
    rm -f run.sh
    rm -f main.nf
    rm -f nextflow.config
    rm -f top_100_structures.txt
    rm -f top_100_reference.txt
    rm -rf results/
    rm -r nf_files/
}

nextflow run . -with-docker ${docker_image}

check_for_successful_run_with_outputs
check_output_model_size
check_importances_size
check_importance_scores_average
check_importance_cells_overlap
clean
