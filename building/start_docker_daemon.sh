
TIMEOUT_SECONDS=20

kernel_name=$(uname -s)
docker_daemon_start_command=""
case "$kernel_name" in
    "Darwin")
        docker_daemon_start_command="open -g -a Docker.app"
    ;;
    "Linux"|*)
        initialization_utility=$(ps --no-headers -o comm 1)
        case "$initialization_utility" in
            "systemd")
                docker_daemon_start_command="sudo systemctl start docker"
            ;;
            "init")
                docker_daemon_start_command="sudo service docker start"
            ;;
        esac
    ;;
esac

function check_docker_daemon_is_running() {
    docker stats --no-stream >/dev/null 2>&1;
    docker_daemon_is_running="$?"
}

if [[ "$docker_daemon_start_command" == "" ]];
then
    check_docker_daemon_is_running
    if [[ "$docker_daemon_is_running" == "0" ]];
    then
        exit
    else
        exit 2
    fi
fi

$docker_daemon_start_command

i=0
check_docker_daemon_is_running
while [[ "$docker_daemon_is_running" == "1" ]] ;
do
    i=$((i+1))
    sleep 1
    if [ $i -gt $TIMEOUT_SECONDS ];
    then
        exit 1
    fi
    check_docker_daemon_is_running
done
