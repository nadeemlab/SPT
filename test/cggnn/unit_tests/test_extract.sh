spt cggnn extract \
    --database-config-file ../db/.spt_db.config.container \
    --study-name "Melanoma intralesional IL2" \
    --output_directory .
$([ $? -eq 0 ] && [ -e "Melanoma intralesional IL2/label_to_result.json" ] && [ -e "Melanoma intralesional IL2/cells.h5" ] && [ -e "Melanoma intralesional IL2/labels.h5" ])
status="$?"
[ $status -eq 0 ] || echo "cggnn extract failed."

cat "Melanoma intralesional IL2/label_to_result.json"
python3.11 -c 'import pandas as pd; print(pd.read_hdf("Melanoma intralesional IL2/cells.h5"))'
python3.11 -c 'import pandas as pd; print(pd.read_hdf("Melanoma intralesional IL2/labels.h5"))'

rm -r "Melanoma intralesional IL2/"

if [ $status -eq 0 ];
then
    exit 0
else
    exit 1
fi
