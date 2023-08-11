
blue="\033[36;2m"
green="\033[32m"
yellow="\033[33m"
red="\033[31m"
reset_code="\033[0m"

function test_squidpy() {
    feature_class="$1"
    if [[ "$feature_class" == "neighborhood%20enrichment" ]];
    then
        p1="$2"
        p2="$3"
        filename="$4"
        query="http://spt-apiserver-testing:8080/request-squidpy-computation/?study=Melanoma%20intralesional%20IL2&phenotype=$p1&phenotype=$p2&feature_class=$feature_class"
    fi
    if [[ "$feature_class" == "ripley" ]];
    then
        p="$2"
        filename="$3"
        query="http://spt-apiserver-testing:8080/request-squidpy-computation/?study=Melanoma%20intralesional%20IL2&phenotype=$p&feature_class=$feature_class"
    fi
    if [[ "$feature_class" == "co-occurrence" ]];
    then
        p1="$2"
        p2="$3"
        r="$4"
        filename="$5"
        query="http://spt-apiserver-testing:8080/request-squidpy-computation/?study=Melanoma%20intralesional%20IL2&phenotype=$p1&phenotype=$p2&radius=$r&feature_class=$feature_class"
    fi
    start=$SECONDS
    while (( SECONDS - start < 30 )); do
        echo -en "Doing query $blue$query$reset_code ... "
        curl -s "$query" > _squidpy.json;
        if [ "$?" -gt 0 ];
        then
            echo -e "${red}Error with apiserver query.$reset_code"
            cat _squidpy.json
            rm _squidpy.json
            exit 1
        fi
        pending=$(python -c 'import json; o=json.loads(open("_squidpy.json").read()); print(o["is_pending"])')
        if [[ "$pending" == "False" ]];
        then
            echo
            echo -en "${yellow}Metrics available.$reset_code "
            cat _squidpy.json | python -m json.tool > squidpy.json
            rm _squidpy.json
            break
        else
            waitperiod=1.0
            echo "Still pending. Waiting ${waitperiod} seconds to poll for metrics availability... "
            sleep $waitperiod
        fi
    done

    diff $filename squidpy.json
    status=$?
    [ $status -eq 0 ] || (echo "API query for squidpy metrics failed."; )
    if [ $status -eq 0 ];
    then
        rm squidpy.json
        echo -e "${green}Artifact matches.$reset_code"
        echo
    else
        echo -e "${red}Some error with the diff command.$reset_code"
        cat squidpy.json
        rm squidpy.json
        exit 1
    fi
}

test_squidpy "neighborhood%20enrichment" 1 2 module_tests/expected_squidpy1.json
test_squidpy "neighborhood%20enrichment" 2 CD20 module_tests/expected_squidpy2.json
test_squidpy "neighborhood%20enrichment" CD3 CD20 module_tests/expected_squidpy3.json
test_squidpy "co-occurrence" CD3 CD20 50 module_tests/expected_squidpy4.json
test_squidpy "ripley" CD3 module_tests/expected_squidpy5.json
