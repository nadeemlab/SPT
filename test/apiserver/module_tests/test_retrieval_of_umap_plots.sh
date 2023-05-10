
query="http://spt-apiserver-testing:8080/visualization-plots/?study=Melanoma%20intralesional%20IL2"

curl -s "$query" > _rows.json ;
if [ "$?" -gt 0 ];
then
    echo "Error with apiserver query."
    curl "$query"
    exit 1
fi
<<<<<<< HEAD

size=$(stat -c "%s" _rows.json)
if [ $size -lt 1000000 ];
then
    echo "JSON file ($size bytes) is less than 1MB in size, as expected."
    rm _rows.json
else
    echo "JSON file is unexpectedly large: $size bytes."
    exit 1
fi
=======
rm _rows.json
>>>>>>> main
