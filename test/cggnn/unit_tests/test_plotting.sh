spt cggnn plot-interactives \
    --cg_path unit_tests/ \
    --output_directory . \
    --merge_rois
plotting_ran="$?"

[ $? -eq 0 ] && [ $(ls "interactives/"* 2> /dev/null | wc -l) -eq 30 ]
thirty_created="$?"

rm -r "interactives/"

if [ $plotting_ran -eq 0 ] && [ $thirty_created -eq 0 ];
then
    exit 0
else
    exit 1
fi