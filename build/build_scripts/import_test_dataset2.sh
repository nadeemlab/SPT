
cat build/build_scripts/.workflow.config2 | sed 's/YYY/2/g' > .workflow.config
spt workflow configure --workflow='tabular import' --config-file=.workflow.config
nextflow run .
spt graphs upload-importances --config_path=build/build_scripts/.graph.config2 --importances_csv_path test/test_data/gnn_importances/2.csv
cat work/*/*/.command.log
