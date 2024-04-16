
spt workflow configure --workflow='reduction visual' --config-file=module_tests/.workflow.config
nextflow run .

status=$?

cat work/*/*/.command.log

rm -f .nextflow.log*; rm -rf .nextflow/; rm -f configure.sh; rm -f run.sh; rm -f main.nf; rm -f nextflow.config; rm -rf work/; rm -rf results/

if [ $status -gt 0 ] ;
then
    echo "Error during nextflow run." >&2
    exit 1
fi

python module_tests/create_plots_page.py "Melanoma intralesional IL2 collection: abc-123" ../db/.spt_db.config.container > plots.html
