#!/bin/bash
# The "download.sh" script should typically fetch a big source data file.
# Something like:
#     wget https://data-repository-hub.com/123456789/SourceData_March_10_2023.zip
#
# In this dummy example case we'll pretend this (committed) zip file was downloaded by this script:
#     SourceData_March_10_2023.zip
#
# Prefer NOT to commit such downloaded files, even to git LFS.
main_source_file=SourceData_March_10_2023.zip
if [[ -f $main_source_file ]];
then
    echo "$main_source_file is present."
else
    echo "Error: $main_source_file is not present. Not downloaded?"
    exit 1
fi
