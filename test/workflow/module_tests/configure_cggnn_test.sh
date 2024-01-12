cd workflow
spt workflow configure --workflow='cg-gnn' --config-file=module_tests/.workflow.config
echo -e "\ndocker.runOptions = '--network workflow_isolated_temporary_test'\n" >> nextflow.config
