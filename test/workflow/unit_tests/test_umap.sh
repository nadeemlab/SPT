
spt workflow configure --local --workflow='reduction visual' --study-name='Melanoma intralesional IL2' --database-config-file=../db/.spt_db.config.container
nextflow run .

status=$?

cat work/*/*/.command.log

rm -f .nextflow.log*; rm -rf .nextflow/; rm -f configure.sh; rm -f run.sh; rm -f main.nf; rm -f nextflow.config; rm -rf work/; rm -rf results/

if [ $? -gt 0 ] ;
then
    echo "Error during nextflow run." >&2
    exit 1
fi

python unit_tests/create_plots_page.py "Melanoma intralesional IL2" ../db/.spt_db.config.container > plots.html

diff plots.html unit_tests/expected_plots.html
status=$?
if [ $status -gt 0 ] ;
then
    echo "Not exactly expected UMAP page." >&2
    cat plots.html >&2
    rm plots.html
    exit 1
fi
rm plots.html
