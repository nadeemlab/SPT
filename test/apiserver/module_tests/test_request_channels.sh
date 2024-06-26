query="http://spt-apiserver-testing:8080/channels/?study=Melanoma%20intralesional%20IL2"

curl -s $query | python -m json.tool | tee summary.json | tr '\n' ' ' | sed 's/ \+//g'
if [ "$?" -gt 0 ];
then
    echo "Error with apiserver query."
    curl $query
    exit 1
fi

diff module_tests/expected_channels.json summary.json
status=$?
[ $status -eq 0 ] || (echo "API query for phenotype summary failed."; )

if [ $status -eq 0 ];
then
        rm summary.json
    exit 0
else
        cat summary.json
        rm summary.json
    exit 1
fi
