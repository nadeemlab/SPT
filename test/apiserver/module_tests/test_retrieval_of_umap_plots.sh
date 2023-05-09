
query="http://spt-apiserver-testing:8080/visualization-plots/?study=Melanoma%20intralesional%20IL2"

curl -s "$query" > _rows.json ;
if [ "$?" -gt 0 ];
then
    echo "Error with apiserver query."
    curl "$query"
    exit 1
fi
rm _rows.json
