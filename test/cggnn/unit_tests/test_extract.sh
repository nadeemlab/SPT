spt cggnn extract \
    --config_path unit_tests/spt-test.config \
    --output_directory .
$([ $? -eq 0 ] && [ -e "label_to_result.json" ] && [ -e "cells.h5" ] && [ -e "labels.h5" ])
status="$?"
[ $status -eq 0 ] || echo "cggnn extract failed."

cat "label_to_result.json"
python3.11 -c 'import pandas as pd; print(pd.read_hdf("cells.h5"))'
python3.11 -c 'import pandas as pd; print(pd.read_hdf("labels.h5"))'

rm "label_to_result.json"; rm "cells.h5"; rm "labels.h5"

if [ $status -eq 0 ];
then
    exit 0
else
    exit 1
fi
