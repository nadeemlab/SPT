
spt db create-schema --database-config-file=build/db/.spt_db.config.local

spt workflow configure --local --input-path test/test_data/adi_preprocessed_tables/dataset2/ --workflow='tabular import' --database-config-file build/db/.spt_db.config.local
nextflow run .
spt cggnn upload-importances --study "Breast cancer IMC" --spt_db_config_location build/db/.spt_db.config.local --importances_csv_path test/test_data/gnn_importances/2.csv
cat work/*/*/.command.log
