
blue="\033[36;2m"
green="\033[32m"
yellow="\033[33m"
red="\033[31m"
reset_code="\033[0m"

function normalize_floats() {
    filename="$1"
    sed -r 's/(\.[0-9][0-9][0-9])[0-9]+/\1/g' "$filename"
}

function signature_query_form() {
    ordinality="$2"
    if [[ "$ordinality" == "2" ]];
    then
        variable_name_positive="positive_marker2"
        variable_name_negative="negative_marker2"
    else
        variable_name_positive="positive_marker"
        variable_name_negative="negative_marker"
    fi
    signature="$1"
    form=$(echo "$signature" | sed "s/\(\([a-zA-Z0-9]*\)+\)/$variable_name_positive=\2\&/g")
    if [[ "$signature" == "$form" ]];
    then
        form=$(echo "$signature" | sed "s/\(\([a-zA-Z0-9]*\)-\)/$variable_name_negative=\2\&/g")
    fi
    echo "$form" | sed 's/.$//'
}

function test_squidpy_custom_phenotypes() {
    feature_class="$1"
    p1_positive="$2"
    p1_negative="$3"
    if [[ "$p1_negative" == " " ]];
    then
        part1=$(signature_query_form "$p1_positive")"&"$(signature_query_form "")
    else
        part1=$(signature_query_form "$p1_positive")"&"$(signature_query_form "$p1_negative")
    fi
    if [[ "$feature_class" == "neighborhood%20enrichment" || "$feature_class" == "co-occurrence" ]];
    then
        p2_positive="$4"
        p2_negative="$5"

        if [[ "$p2_negative" == " " ]];
        then
            part2=$(signature_query_form "$p2_positive" "2")"&"$(signature_query_form "" "2")
        else
            part2=$(signature_query_form "$p2_positive" "2")"&"$(signature_query_form "$p2_negative" "2")
        fi
        phenotype_query="$part1&$part2"
    else
        phenotype_query="$part1"
    fi

    endpoint="request-spatial-metrics-computation-custom-phenotype"
    if [[ "$feature_class" == "neighborhood%20enrichment" || "$feature_class" == "co-occurrence" ]];
    then
        endpoint="${endpoint}s"
    fi
    query="http://spt-apiserver-testing:8080/$endpoint/?study=Melanoma%20intralesional%20IL2&$phenotype_query&feature_class=$feature_class"

    if [[ "$feature_class" == "co-occurrence" ]];
    then
        radius="$6"
        query="$query&radius=$radius"
    fi

    if [[ "$feature_class" == "neighborhood%20enrichment" ]];
    then
        filename="$6"
    fi
    if [[ "$feature_class" == "co-occurrence" ]];
    then
        filename="$7"
    fi
    if [[ "$feature_class" == "ripley" ]];
    then
        filename="$4"
    fi
    if [[ "$feature_class" == "spatial%20autocorrelation" ]];
    then
        filename="$4"
    fi

    start=$SECONDS
    while (( SECONDS - start < 300 )); do
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
            waitperiod=5.0
            echo "Still pending. Waiting ${waitperiod} seconds to poll for metrics availability... "
            sleep $waitperiod
        fi
    done
    if [ ! -f squidpy.json ];
    then
        echo "Test timed out."
        exit 1
    fi;

    normalize_floats "$filename" > n1.json
    normalize_floats squidpy.json > n2.json
    diff n1.json n2.json
    status=$?
    rm n1.json n2.json
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

test_squidpy_custom_phenotypes "neighborhood%20enrichment" "SOX10+" "CD20-CD3-CD4-CD8-FOXP3-" "CD3+CD4+" "CD20-CD56-CD8-FOXP3-SOX10-" module_tests/expected_squidpy1.json
test_squidpy_custom_phenotypes "co-occurrence" "CD3+" "-" "CD20+" "-" 50 module_tests/expected_squidpy4.json
test_squidpy_custom_phenotypes "spatial%20autocorrelation" "CD3+" "-" module_tests/expected_squidpy6.json
