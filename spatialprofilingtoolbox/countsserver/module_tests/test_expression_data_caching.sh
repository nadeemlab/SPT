
function consider_exit() {
    if [[ "$1" != "0" ]];
    then
        exit 1
    fi
}

spt db create-schema --database-config-file ../db/.spt_db.config.container --force
spt workflow configure --local --input-path ../test_data/adi_preprocessed_tables/dataset1/ --workflow='HALO import' --database-config-file ../db/.spt_db.config.container; nextflow run .
spt workflow configure --local --input-path ../test_data/adi_preprocessed_tables/dataset2/ --workflow='HALO import' --database-config-file ../db/.spt_db.config.container; nextflow run .

mkdir expression_data
cd expression_data
spt countsserver cache-expressions-data-array --database-config-file ../../db/.spt_db.config.container

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
        diff "../../expression_data/$f" $f
        consider_exit $?
        echo "File $f generated as expected with correct contents."
    fi
done

cd ../../
rm -rf expression_data/