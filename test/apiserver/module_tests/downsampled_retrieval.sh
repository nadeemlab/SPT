#!/bin/bash

function get_downsampled() {
    study="$1"
    server="$2"

    # Retrieve precomputed subsample
    curl "http://$server/cell-data-binary-intensity-whole-study-subsample/?study=$study" --header "Accept-Encoding: br" | brotli -d - > response_decompressed.bin

    # File separator byte
    fs=$(xxd -r <<<'0 1c')

    # Locate file separator
    offset=$(grep --byte-offset -o -a "$fs" response_decompressed.bin | head -n1 | cut -f1 -d':')
    echo "Offset: $offset"

    # Save JSON metadata section
    head -c $offset response_decompressed.bin  | python -m json.tool > metadata.json
    echo "Saved metadata.json"

    number_channels=$(jq '.channel_order_and_thresholds | length' metadata.json)

    # Save readable representation of binary section
    offset2=$(( offset + 2 ))
    tail -c +$offset2 response_decompressed.bin | xxd -b -c $number_channels > rows.txt
    echo "Saved rows.txt"
}
