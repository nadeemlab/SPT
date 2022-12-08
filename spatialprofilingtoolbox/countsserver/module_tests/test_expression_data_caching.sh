
function consider_exit() {
    if [[ "$1" != "0" ]];
    then
        exit 1
    fi
}

rm -rf expression_data/
mkdir expression_data
cd expression_data
spt countsserver cache-expressions-data-array --database-config-file ../../db/.spt_db.config.container
if [[ "$?" != "0" ]];
then
    echo "Caching of expressions data array failed."
    exit 1
fi

expressions_dir=../module_tests/expected_binary_expression_data_cohoused
for f in *;
do
    if [ ! -f "$expressions_dir/$f" ];
    then
        echo "Test script created unexpected file: $f"
        exit 1
    fi
done

cd $expressions_dir
for f in *;
do
    if [ ! -f "../../expression_data/$f" ];
    then
        echo "Test script failed to create expected file: $f"
        exit 1
    else
        echo "$f" | grep -q '\.bin$'
        if [[ "$?" == "0" ]];
        then
            bash ../check_binary_expressions_equivalent.sh "../../expression_data/$f" $f
            consider_exit $?
        else
            diff "../../expression_data/$f" $f
            result=$?
            echo "File ../../expression_data/$f"
            cat "../../expression_data/$f"
            echo ''
            echo "File $f"
            cat $f
            consider_exit $result
            echo "File $f generated as expected with correct contents."
        fi
    fi
done

cd ../../
rm -rf expression_data/
