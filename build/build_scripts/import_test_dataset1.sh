
spt workflow configure --local --input-path test/test_data/adi_preprocessed_tables/dataset1/ --workflow='tabular import' --database-config-file build/db/.spt_db.config.local
nextflow run .
cat work/*/*/.command.log

spt workflow configure --local --workflow='reduction visual' --study-name='Melanoma intralesional IL2' --database-config-file=build/db/.spt_db.config.local
nextflow run .
rm -f .nextflow.log*; rm -rf .nextflow/; rm -f configure.sh; rm -f run.sh; rm -f main.nf; rm -f nextflow.config; rm -rf work/; rm -rf results/

spt cggnn upload-importances --study-name "Melanoma intralesional IL2" --database-config-file build/db/.spt_db.config.local --importances_csv_path test/test_data/gnn_importances/1.csv

spt db status --database-config-file build/db/.spt_db.config.local > table_counts.txt
diff build/build_scripts/expected_table_counts.txt table_counts.txt
status=$?
[ $status -eq 0 ] && echo "Import created correct number of records." || (cat table_counts.txt && echo "Import failed.")
rm table_counts.txt

if [ $status -eq 0 ];
then
    exit 0
else
    exit 1
fi
