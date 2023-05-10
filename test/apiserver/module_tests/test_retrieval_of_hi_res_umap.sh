
query="http://spt-apiserver-testing:8080/visualization-plot-high-resolution/?study=Melanoma%20intralesional%20IL2&channel=CD8"

curl -s "$query" > hi_res.png ;
if [ "$?" -gt 0 ];
then
    echo "Error with apiserver query for high resolution image."
    echo "$query"
    exit 1
fi

size=$(stat -f%z hi_res.png)
rm hi_res.png
if [ $ss -lt 1500000 ];
    echo "PNG file is at least 1.5MB, as expected."
then
    echo "PNG file is unexpectedly small."
    exit 1
fi
