#!/bin/bash

supplementbase="sciimmunol.abi5072_tables_s1 to_s5"
rm -rf CP_output_tiff/
rm "$supplementbase.xlsx"

if [[ "$1" == "downloads" ]];
then
    rm "$supplementbase.zip"
    mv Moldoveanu2022-cytof-RAW.tar.gz Moldoveanu2022-cytof-RAW.tar.gz.bak
    echo "Moving Moldoveanu2022-cytof-RAW.tar.gz to backup. Delete if you want."
fi
