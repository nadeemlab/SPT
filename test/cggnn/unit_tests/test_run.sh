spt cggnn run \
    --measurement_study "Melanoma intralesional IL2 (Hollmann lab) - measurement" \
    --analysis_study "Melanoma intralesional IL2 (Hollmann lab) - data analysis" \
    --specimen_study "Melanoma intralesional IL2 (Hollmann lab) - specimen collection" \
    --host spt-db-testing \
    --dbname postgres \
    --user postgres \
    --password postgres \
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
