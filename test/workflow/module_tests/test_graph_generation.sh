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

rm -r "results/"
rm -r "nf_files/"
