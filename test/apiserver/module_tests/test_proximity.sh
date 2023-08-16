
blue="\033[36;2m"
green="\033[32m"
yellow="\033[33m"
red="\033[31m"
reset_code="\033[0m"

function test_proximity() {
    p1="$1"
    p2="$2"
    r="$3"
    filename="$4"
    query="http://spt-apiserver-testing:8080/request-phenotype-proximity-computation/?study=Melanoma%20intralesional%20IL2&phenotype1=$p1&phenotype2=$p2&radius=$r"
    start=$SECONDS
    while (( SECONDS - start < 15 )); do
        echo -en "Doing query $blue$query$reset_code ... "
        curl -s "$query" > _proximity.json;
        if [ "$?" -gt 0 ];
        then
            echo -e "${red}Error with apiserver query.$reset_code"
            cat _proximity.json
            rm _proximity.json
            exit 1
        fi
        pending=$(python -c 'import json; o=json.loads(open("_proximity.json").read()); print(o["is_pending"])')
        if [[ "$pending" == "False" ]];
        then
            echo
            echo -en "${yellow}Metrics available.$reset_code "
            cat _proximity.json | python -m json.tool > proximity.json
            rm _proximity.json
            break
        else
            waitperiod=1
            echo "Still pending. Waiting ${waitperiod} seconds to poll for metrics availability... "
            sleep $waitperiod
        fi
    done

    diff $filename proximity.json
    status=$?
    [ $status -eq 0 ] || (echo "API query for proximity metrics failed."; )
    if [ $status -eq 0 ];
    then
        rm proximity.json
        echo -e "${green}Artifact matches.$reset_code"
        echo
    else
        echo -e "${red}Some error with the diff command.$reset_code"
        cat proximity.json
        rm proximity.json
        exit 1
    fi
}

test_proximity B2M CD4 60 module_tests/expected_proximity.json
test_proximity B7H3 2 60 module_tests/expected_proximity2.json
test_proximity CD8 MHCI 125 module_tests/expected_proximity3.json
test_proximity 3 PD1 125 module_tests/expected_proximity4.json
