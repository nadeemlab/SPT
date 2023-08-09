spt cggnn extract \
    --spt_db_config_location ../db/.spt_db.config.container \
    --study "Melanoma intralesional IL2" \
    --output_location .
status=$([ $? ] && [ -e "label_to_results.json" ] && [ -e "cells.h5" ] && [ -e "labels.h5" ])
[ $status -eq 0 ] || echo "cggnn extract failed."

if [ $status -eq 0 ];
then
    exit 0
else
    exit 1
fi
