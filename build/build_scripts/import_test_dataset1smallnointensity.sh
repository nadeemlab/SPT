
spt workflow configure --local --input-path test/test_data/adi_preprocessed_tables/dataset3/ --workflow='tabular import' --database-config-file build/db/.spt_db.config.local
nextflow run .

spt graphs upload-importances --study-name "Melanoma intralesional IL2" --database-config-file build/db/.spt_db.config.local --importances_csv_path test/test_data/gnn_importances/3.csv

cat work/*/*/.command.log
spt db status --database-config-file build/db/.spt_db.config.local > table_counts.txt
diff build/build_scripts/expected_table_counts_1small.txt table_counts.txt
status=$?
[ $status -eq 0 ] && echo "Import created correct number of records." || echo "Import failed."
rm table_counts.txt

if [ $status -eq 0 ];
then
    exit 0
else
    exit 1
fi
