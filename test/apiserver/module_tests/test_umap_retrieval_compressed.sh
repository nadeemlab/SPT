
blue="\033[36;2m"
green="\033[32m"
yellow="\033[33m"
red="\033[31m"
reset_code="\033[0m"

function test_cell_data_binary_compressed() {
    study="$1"
    sample="$2"
    query="http://spt-apiserver-testing-apiserver:8080/cell-data-binary/?study=$study&sample=$sample"

    echo -e "Doing query $blue$query$reset_code ... "
    curl -s "$query"  > _celldata.bin;
    cat _celldata.bin | tail -c +21 | xxd -e -b -c 20 > _celldata.dump
    rm _celldata.bin

    echo -e "Doing query $blue$query$reset_code with "br" header ... "
    curl -s -H "Accept-Encoding: br" "$query" > _celldata.brotli.bin;
    cat _celldata.brotli.bin | brotli --decompress > _celldata.bin2
    cat _celldata.bin2 | tail -c +21 | xxd -e -b -c 20 > _celldata.dump2
    rm _celldata.brotli.bin
    rm _celldata.bin2

    diff _celldata.dump _celldata.dump2
    status=$?
    rm _celldata.dump
    rm _celldata.dump2

    if [ "$?" -gt 0 ];
    then
        echo -e "${red}Error comparing response with and without compression.$reset_code"
        exit 1
    fi
}

test_cell_data_binary_compressed "Melanoma+intralesional+IL2" "UMAP+virtual+sample"
