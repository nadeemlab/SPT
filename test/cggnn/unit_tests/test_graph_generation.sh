spt cggnn generate-graphs \
    --spt_hdf_cell_path unit_tests/cells.h5 \
    --spt_hdf_label_path unit_tests/labels.h5 \
    --validation_data_percent 15 \
    --test_data_percent 15 \
    --output_directory graphs/ \
    --random_seed 0
generation_ran="$?"

[ -e "graphs/feature_names.txt" ] && [ -e "graphs/graphs.pkl" ]
files_exist="$?"

if [ $generation_ran -ne 0 ] && [ $files_exist -ne 0 ];
then
    exit 1
fi

cat "graphs/feature_names.txt"
python3.11 -c 'from spatialprofilingtoolbox.cggnn.util import load_hs_graphs; graphs, _ = load_hs_graphs("graphs/"); assert len(graphs) == 30, f"Graph count ({len(graphs)}) doesn\t match true value (30).";'
lengths_ok="$?"

rm -r "graphs/"

if [ $lengths_ok -eq 0 ];
then
    exit 0
else
    exit 1
fi
