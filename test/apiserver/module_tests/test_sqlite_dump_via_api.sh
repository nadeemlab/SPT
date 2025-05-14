
study="Melanoma+intralesional+IL2"

query="http://spt-apiserver-testing-apiserver:8080/sqlite/?study=$study"
curl -s "$query"
status=$?
if [ $status -gt 0 ];
then
    exit $status
fi;

query="http://spt-apiserver-testing-apiserver:8080/sqlite/?study=$study&no_feature_values="
curl -s "$query"
status=$?
if [ $status -gt 0 ];
then
    exit $status
fi;

query="http://spt-apiserver-testing-apiserver:8080/sqlite/?study=$study&no_feature_values=&no_feature_specifications="
curl -s "$query"
status=$?
if [ $status -gt 0 ];
then
    exit $status
fi;
