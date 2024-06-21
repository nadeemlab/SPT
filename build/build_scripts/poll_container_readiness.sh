
declare -A expectedmessages
expectedmessages[spt-apiserver-testing]="Uvicorn running on"
expectedmessages[spt-ondemand--testing]="Listening on new_items_in_queue channel"
expectedmessages[spt-ondemand-testing2]="Listening on new_items_in_queue channel"
expectedmessages[spt-db---testing-only]="database system is ready to accept connections"
expectedmessages[spt--workflow-testing]="workflow container is ready to work"
expectedmessages[temporary-spt-db-preloading]="database system is ready to accept connections"

container_wait_time=60 #seconds
counter=1
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
    if [[ $counter -gt $container_wait_time ]];
    then
        echo "Container readiness checking timed out after $container_wait_time seconds"
        exit 1
    fi
    sleep 1
done

echo "Containers may not be ready"
exit 1