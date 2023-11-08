spt cggnn generate-graphs \
    --spt_hdf_cell_filename cells.h5 \
    --spt_hdf_label_filename labels.h5 \
    --validation_data_percent 15 \
    --test_data_percent 15 \
    --output_directory . \
    --random_seed 0
$([ $? -eq 0 ] && [ -e "feature_names.txt" ] && [ -e "graphs.bin" ] && [ -e "graph_info.pkl" ])
status="$?"
echo "Status: $status"
[ $status -eq 0 ] || echo "cggnn generate-graphs failed."

cat "feature_names.txt"
python3.11 -c 'from spatialprofilingtoolbox.cggnn.util import load_cell_graphs; graphs, graph_info = load_cell_graphs("."); assert len(graphs) == len(graph_info) == 30;'

rm -r "."

if [ $status -eq 0 ];
then
    exit 0
else
    exit 1
fi
