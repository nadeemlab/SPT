#!/bin/bash

mkdir -p generated_artifacts/

if [[ ! -d CP_output_tiff ]];
then
    filebase="Moldoveanu2022-cytof-RAW"
    gunzip -c "$filebase.tar.gz" >$filebase.tar
    tar -xvf "$filebase.tar"
    for f in $(find CP_output_tiff/ | grep '/\._'); do rm -rf "$f"; done
fi

if [[ ! -f "sciimmunol.abi5072_tables_s1 to_s5.xlsx" ]];
then
    supplement_file="sciimmunol.abi5072_tables_s1 to_s5.zip"
    unzip "$supplement_file"
fi

cp manually_created/composite_phenotypes.csv generated_artifacts/
cp manually_created/study.json generated_artifacts/study.json
python extract.py $@
