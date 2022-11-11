
spt workflow configure --local --input-path spatialprofilingtoolbox/test_data/adi_preprocessed_tables/dataset2/ --workflow='HALO import' --database-config-file spatialprofilingtoolbox/db/.spt_db.config.local
nextflow run .
cat work/*/*/.command.log
