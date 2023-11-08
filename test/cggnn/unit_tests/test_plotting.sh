spt cggnn plot-interactives \
    --cg_path . \
    --output_directory . \
    --merge_rois
$([ $? -eq 0 ] && [ $(ls "interactives/"* 2> /dev/null | wc -l) -eq 30 ])
status="$?"
echo "Status: $status"
[ $status -eq 0 ] || echo "cggnn plot-interactives failed."

rm -r "."

if [ $status -eq 0 ];
then
    exit 0
else
    exit 1
fi
