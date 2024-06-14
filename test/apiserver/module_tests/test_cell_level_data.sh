
blue="\033[36;2m"
green="\033[32m"
yellow="\033[33m"
red="\033[31m"
reset_code="\033[0m"

function test_cell_data_binary() {
    study="$1"
    sample="$2"
    filename="$3"
    query="http://spt-apiserver-testing:8080/cell-data-binary/?study=$study&sample=$sample"

    echo -e "Doing query $blue$query$reset_code ... "
    curl -s "$query"  > _celldata.bin;
    if [ "$?" -gt 0 ];
    then
        echo -e "${red}Error with apiserver query.$reset_code"
        echo "Result saved to file: _celldata.bin"
        exit 1
    fi

    cat _celldata.bin | tail -c +21 | xxd -e -b -c 20 > _celldata.dump
    rm _celldata.bin

    diff $filename _celldata.dump

    status=$?
    [ $status -eq 0 ] || (echo "API query for cell data failed, unexpected contents."; )
    if [ $status -eq 0 ];
    then
        rm _celldata.dump
        echo -e "${green}Artifact matches.$reset_code"
        echo
    else
        echo -e "${red}Some error with the diff command.$reset_code"
        echo "Erroneous file saved to: _celldata.dump"
        exit 1
    fi
}

function test_feature_names_retrieval() {
    study="$1"
    query="http://spt-apiserver-testing:8080/cell-data-binary-feature-names/?study=$study"

    echo -e "Doing query $blue$query$reset_code ... "
    curl -s "$query" | python -m json.tool > _names.json;
    if [ "$?" -gt 0 ];
    then
        echo -e "${red}Error with apiserver query.$reset_code"
        echo "Result saved to file: _names.json"
        exit 1
    fi

    diff module_tests/expected_bitmask_feature_names.json _names.json

    status=$?
    [ $status -eq 0 ] || (echo "API query for cell data failed, unexpected contents."; )
    if [ $status -eq 0 ];
    then
        rm _names.json
        echo -e "${green}Artifact matches.$reset_code"
        echo
    else
        echo -e "${red}Some error with the diff command.$reset_code"
        cat _names.json
        echo "Erroneous file saved to: _names.json"
        exit 1
    fi
}

function test_missing_case() {
    study=$1
    sample=$2
    query="http://spt-apiserver-testing:8080/cell-data/?study=$study&sample=$sample"
    echo -e "Doing query $blue$query$reset_code ... "
    curl -s "$query" > result.txt
    cat result.txt
    diff result.txt module_tests/expected_error.txt 1>/dev/null 2>/dev/null
    status=$?
    rm result.txt
    if [ ! $status -eq 0 ];
    then
        echo "Did not get the expected error message in case of missing sample."
        exit 1
    else
        echo -n " Got expected error message in case of missing sample. "
        echo -e "${green}Artifact matches.$reset_code"
    fi
}

test_missing_case "Melanoma+intralesional+IL2" "ABC"

test_cell_data_binary "Melanoma+intralesional+IL2" "lesion+0_1" module_tests/celldata.dump
test_feature_names_retrieval "Melanoma+intralesional+IL2"
