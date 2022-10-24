
query=http://spt-apiserver-testing:8080/specimen-measurement-study-names
curl -s $query ;
if [ "$?" -gt 0 ];
then
    echo "Error with apiserver query."
    curl $query
    exit 1
fi

curl -s $query | python -m json.tool > names.json

diff module_tests/expected_specimen_measurement_study_names.json names.json
status=$?
[ $status -eq 0 ] || (echo "API query for measurement study names failed."; )
rm names.json

if [ $status -eq 0 ];
then
    exit 0
else
    exit 1
fi
