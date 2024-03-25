
boldgreen="\033[32;1m"
regulargreen="\033[32m"
reset="\033[0m"

function print_heading_line(){
    echo -e "$boldgreen$1$reset"
}

function print_regular_line(){
    echo -e "$regulargreen$1$reset"
}
