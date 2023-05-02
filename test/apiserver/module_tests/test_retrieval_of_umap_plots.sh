
query="http://spt-apiserver-testing:8080/visualization-plots/?study=Melanoma%20intralesional%20IL2"

curl -s "$query" > _rows.json ;
if [ "$?" -gt 0 ];
then
    echo "Error with apiserver query."
    curl "$query"
    exit 1
fi
cat _rows.json | python -m json.tool > rows.json; rm _rows.json
diff module_tests/expected_umap_rows.json rows.json
status=$?
[ $status -eq 0 ] || (echo "API query for UMAP visualizations had unexpected response."; )

if [ $status -eq 0 ];
then
	rm rows.json
    exit 0
else
	cat rows.json
	rm rows.json
    exit 1
fi
