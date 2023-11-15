spt cggnn run \
    --study-name "Melanoma intralesional IL2" \
    --database_config_file ../db/.spt_db.config.container \
    --b 8 \
    --epochs 10 \
    --k 3 \
    --merge_rois \
    --prune_misclassified 
status=$?
[ $status -eq 0 ] || echo "cggnn run failed."

if [ $status -eq 0 ];
then
    exit 0
else
    exit 1
fi
