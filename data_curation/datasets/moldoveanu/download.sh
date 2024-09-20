#!/bin/bash

# Download itself may be blocked by the remote servers, you may need to
# do the download step manually then run this script to check hashes.

function do_checksum() {
    filename="$1"
    echo -n "Checking checksum of $filename ... "
    sha256sum "$filename" > temp.txt
    diff temp.txt "$filename.sha256"
    status="$?"
    rm temp.txt
    if [[ $status -eq 0 ]];
    then
        echo "verified, has expected contents."
    else
        echo "failed."
        exit 1
    fi
}

filebase="Moldoveanu2022-cytof-RAW"
if [[ ! -f $filebase.tar.gz ]];
then
    wget "https://zenodo.org/records/5903190/files/$filebase.tar.gz?download=1"
    mv "Moldoveanu2022-cytof-RAW.tar.gz?download=1" "$filebase.tar.gz"
fi

supplement_file="sciimmunol.abi5072_tables_s1 to_s5.zip"
supplement="https://www.science.org/doi/suppl/10.1126/sciimmunol.abi5072/suppl_file/sciimmunol.abi5072_tables_s1%20to_s5.zip"

if [[ ! -f "$supplement_file" ]];
then
    wget "$supplement"
fi

do_checksum $filebase.tar.gz
do_checksum "$supplement_file"
