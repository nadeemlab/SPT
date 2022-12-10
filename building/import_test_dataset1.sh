
spt workflow configure --local --input-path spatialprofilingtoolbox/test_data/adi_preprocessed_tables/dataset1/ --workflow='HALO import' --database-config-file spatialprofilingtoolbox/db/.spt_db.config.local
nextflow run .
cat work/*/*/.command.log
spt db create-schema --refresh-views-only --database-config-file spatialprofilingtoolbox/db/.spt_db.config.local
spt db status --database-config-file spatialprofilingtoolbox/db/.spt_db.config.local > table_counts.txt
diff building/expected_table_counts.txt table_counts.txt
status=$?
[ $status -eq 0 ] && echo "Import created correct number of records." || echo "Import failed."
rm table_counts.txt

if [ $status -eq 0 ];
then
    exit 0
else
    exit 1
fi
