
declare -A expectedmessages
expectedmessages[spt-apiserver-testing]="Uvicorn running on"
expectedmessages[spt-countsserver-testing]="countsserver is ready to accept connections"
expectedmessages[spt-db-testing]="database system is ready to accept connections"
expectedmessages[spt-workflow-testing]="workflow container is ready to work"

counter=0
while :
do
    echo "Attempt $counter to check readiness of containers."
    available="yes"
    for modulename in "$@"
    do
        docker compose logs | grep "$module_name" | grep "${expectedmessages[$modulename]}" 2>/dev/null 1>/dev/null
        if [ $? -gt 0 ];
        then
            available="no"
        fi
    done
    if [[ $available == "yes" ]];
    then
        echo "Containers are ready"
        exit
    fi
    counter=$(( counter + 1 ))
    if [[ $counter -gt 30 ]];
    then
        echo "Container readiness checking timed out after 15 seconds"
        exit 1
    fi
    sleep 0.5
done

echo "Containers may not be ready"
exit 1