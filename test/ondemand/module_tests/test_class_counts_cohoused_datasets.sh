
function consider_exit() {
    if [[ "$1" != "0" ]];
    then
        exit 1
    fi
}

python module_tests/get_class_counts.py 1 > counts1.txt
diff counts1.txt module_tests/expected_counts_structured1.json
status="$?"
cat counts1.txt; echo ''
rm counts1.txt
consider_exit "$status"
echo "Class count example in dataset 1 is correct."; echo ''

python module_tests/get_class_counts.py 2 > counts2.txt
diff counts2.txt module_tests/expected_counts2.json
status="$?"
cat counts2.txt; echo ''
rm counts2.txt
consider_exit "$status"
echo "Class count example in dataset 2 is correct."; echo ''
