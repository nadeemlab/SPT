
query="http://spt-apiserver-testing:8080/request-phenotype-proximity-computation/?study=Melanoma%20intralesional%20IL2&phenotype1=B2M&phenotype2=CD4&radius=60"

curl -s "$query" ;
if [ "$?" -gt 0 ];
then
    echo "Error with apiserver query."
    curl $query
    exit 1
fi

curl -s $query | python -m json.tool > proximity.json

diff module_tests/expected_proximity.json proximity.json
status=$?
[ $status -eq 0 ] || (echo "API query for proximity metrics failed."; )

if [ $status -eq 0 ];
then
	rm proximity.json
else
	cat proximity.json
	rm proximity.json
    exit 1
fi


query="http://spt-apiserver-testing:8080/request-phenotype-proximity-computation/?study=Melanoma%20intralesional%20IL2&phenotype1=B7H3&phenotype2=2&radius=60"

curl -s "$query" ;
if [ "$?" -gt 0 ];
then
    echo "Error with apiserver query."
    curl $query
    exit 1
fi

curl -s $query | python -m json.tool > proximity.json

diff module_tests/expected_proximity2.json proximity.json
status=$?
[ $status -eq 0 ] || (echo "API query for proximity metrics failed."; )

if [ $status -eq 0 ];
then
	rm proximity.json
else
	cat proximity.json
	rm proximity.json
    exit 1
fi
