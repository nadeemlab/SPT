
FM=test/test_data/adi_preprocessed_tables/dataset1/file_manifest.tsv
cp $FM file_manifest.tsv.bak
(cat file_manifest.tsv.bak | grep -vE '(0_2|0_3|6_2|6_3|6_4)') > $FM

spt workflow configure --local --input-path test/test_data/adi_preprocessed_tables/dataset1/ --workflow='tabular import' --database-config-file build/db/.spt_db.config.local
nextflow run .

cp file_manifest.tsv.bak $FM
rm file_manifest.tsv.bak

spt cggnn upload-importances --spt_db_config_location build/db/.spt_db.config.local --importances_csv_path test/test_data/gnn_importances/3.csv

cat work/*/*/.command.log
spt db create-schema --refresh-views-only --database-config-file build/db/.spt_db.config.local
spt db status --database-config-file build/db/.spt_db.config.local > table_counts.txt
diff build/build_scripts/expected_table_counts_1small.txt table_counts.txt
status=$?
[ $status -eq 0 ] && echo "Import created correct number of records." || echo "Import failed."
rm table_counts.txt

spt db index-expressions-table --database-config-file=build/db/.spt_db.config.local

if [ $status -eq 0 ];
then
    exit 0
else
    exit 1
fi
