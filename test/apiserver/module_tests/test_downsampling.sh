
function consider_exit() {
    if [[ "$1" != "0" ]];
    then
        exit 1
    fi
}

spt db cache-subsample 106 --database-config-file .spt_db.config.container --only-uncreated;
source module_tests/downsampled_retrieval.sh

study='Melanoma+intralesional+IL2'
server=spt-apiserver-testing-apiserver:8080

get_downsampled "$study" "$server"

diff module_tests/expected_metadata.json metadata.json
status=$?
if [[ "$status" != "0" ]]; then echo 'Something wrong with metadata.json.'; cat metadata.json; fi;
# rm metadata.json;
consider_exit $status


cp rows.txt module_tests/expected_rows.txt

diff module_tests/expected_rows.txt rows.txt
status=$?
if [[ "$status" != "0" ]]; then echo 'Something wrong with rows.txt.'; cat rows.txt; fi;
# rm rows.txt;
consider_exit $status
