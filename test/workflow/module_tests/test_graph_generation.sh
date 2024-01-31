spt workflow configure --workflow='graph generation' --config-file=module_tests/.workflow.config
nextflow run . || { echo "Error: Nextflow run failed"; exit 1; }

[ -e "results/feature_names.txt" ] || { echo "Error: results/feature_names.txt does not exist"; exit 1; }
cat "results/feature_names.txt"

set -e
python3.11 -c '
from spatialprofilingtoolbox.graphs.util import load_hs_graphs
graphs, _ = load_hs_graphs("results/")
assert len(graphs) == 4, f"Error: Graph count ({len(graphs)}) does not match true value (4)."
'

function clean() {
    rm -f .nextflow.log*
    rm -rf .nextflow/
    rm -f configure.sh
    rm -f run.sh
    rm -f main.nf
    rm -f nextflow.config
    rm -rf results/
    rm -rf nf_files/
}

clean
