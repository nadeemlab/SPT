

cat build/build_scripts/.workflow.config | sed 's/YYY/3/g' > .workflow.config
spt workflow configure --workflow='tabular import' --config-file=.workflow.config
nextflow run .

spt graphs upload-importances --config_path=build/build_scripts/.graph.config --importances_csv_path=test/test_data/gnn_importances/3.csv

spt ondemand cache-expressions-data-array

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
