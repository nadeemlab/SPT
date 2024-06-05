
blue="\033[36;2m"
green="\033[32m"
yellow="\033[33m"
red="\033[31m"
reset_code="\033[0m"

function test_cell_data() {
    study="$1"
    sample="$2"
    filename="$3"
    query="http://spt-apiserver-testing:8080/cell-data/?study=$study&sample=$sample"

    echo -e "Doing query $blue$query$reset_code ... "
    curl -s "$query" | python -m json.tool > _celldata.json;
    if [ "$?" -gt 0 ];
    then
        echo -e "${red}Error with apiserver query.$reset_code"
        cat _celldata.json
        rm _celldata.json
        exit 1
    fi

    diff $filename _celldata.json
    status=$?
    [ $status -eq 0 ] || (echo "API query for cell data failed."; )
    if [ $status -eq 0 ];
    then
        rm _celldata.json
        echo -e "${green}Artifact matches.$reset_code"
        echo
    else
        echo -e "${red}Some error with the diff command.$reset_code"
        cat _celldata.json
        rm _celldata.json
        exit 1
    fi
}

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

    diff $filename _celldata.bin
    status=$?
    [ $status -eq 0 ] || (echo "API query for cell data failed, unexpected contents."; )
    if [ $status -eq 0 ];
    then
        rm _celldata.bin
        echo -e "${green}Artifact matches.$reset_code"
        echo
    else
        echo -e "${red}Some error with the diff command.$reset_code"
        echo "Erroneous file saved to: _celldata.bin"
        rm _celldata.bin
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
    diff result.txt module_tests/expected_error.txt
    status=$?
    rm result.txt
    if [ ! $status -eq 0 ];
    then
        echo "Did not get the expected error message in case of missing sample."
        exit 1
    fi
}

test_cell_data "Melanoma+intralesional+IL2" "lesion+0_1" module_tests/expected_cell_data_1.json
test_missing_case "Melanoma+intralesional+IL2" "ABC"

test_cell_data_binary "Melanoma+intralesional+IL2" "lesion+0_1" module_tests/expected_cell_data_1.json
