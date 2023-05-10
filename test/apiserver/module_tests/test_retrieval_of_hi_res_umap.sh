
query="http://spt-apiserver-testing:8080/visualization-plot-high-resolution/?study=Melanoma%20intralesional%20IL2&channel=CD8"

curl -s "$query" > hi_res.png ;
if [ "$?" -gt 0 ];
then
    echo "Error with apiserver query for high resolution image."
    echo "$query"
    exit 1
fi


png=$(file hi_res.png | grep -o 'PNG image data')
if [[ "$png" == "PNG image data" ]];
then
    echo "Query returned valid PNG image file."
else
    echo "Query did not return valid PNG image file."
fi

dimensions=$(file hi_res.png | grep -o "[0-9]\+ x [0-9]\+")
if [[ "$dimensions" == "2400 x 2400" ]];
then
    echo "Dimensions 2400 x 2400 as expected."
else
    echo "Dimensions '$dimensions' not expected value '2400 x 2400'."
fi

size=$(stat -c "%s" hi_res.png)
if [ $size -gt 100000 ];
then
    echo "PNG file ($size bytes) is at least 100KB in size, as expected."
    rm hi_res.png
else
    echo "PNG file is unexpectedly small: $size bytes."
    exit 1
fi
