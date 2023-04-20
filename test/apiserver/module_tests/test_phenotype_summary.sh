
query="http://spt-apiserver-testing:8080/phenotype-summary/?study=Melanoma%20intralesional%20IL2&pvalue=0.1"

curl -s $query ;
if [ "$?" -gt 0 ];
then
    echo "Error with apiserver query."
    curl $query
    exit 1
fi

# curl -s $query | python -m json.tool > summary.json

exit 1
# diff module_tests/expected_phenotype_summary.json summary.json
# status=$?
# [ $status -eq 0 ] || (echo "API query for phenotype summary failed."; )

# if [ $status -eq 0 ];
# then
# 	rm summary.json
#     exit 0
# else
# 	cat summary.json
# 	rm summary.json
#     exit 1
# fi
