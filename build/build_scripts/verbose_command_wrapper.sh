initiation_color_code="\033[0m"
dots_color="\033[33m"
completion_color_code="\033[32;1m"
error_color_code="\033[31;1m"
time_color_code="\033[35;2m"
reset_code="\033[0m"
desired_dots_ending_column=80
status_message_size_limit=15

function display_initiation_message() {
    echo -en "$initiation_color_code"
    echo -en "$1 "
    padchar=.
    echo -e "$reset_code$dots_color""$padchar$padchar$padchar""$reset_code"
}

function display_completion_message() {
    premessage="$3"
    # printf "$premessage"
    echo -en "\x1B[38;5;248m$premessage\x1B[0m"
    _print_dots ${#premessage}

    pad_string_and_wrap_with_code "$1" "$completion_color_code" $status_message_size_limit
    display_transpired_seconds $2
}

function display_error_message() {
    premessage="$3"
    # printf "$premessage"
    echo -en "\x1B[38;5;248m$premessage\x1B[0m"
    _print_dots ${#premessage}

    pad_string_and_wrap_with_code "$1" "$error_color_code" $status_message_size_limit
    display_transpired_seconds $2
}

function display_transpired_seconds() {
    transpired_seconds=$1
    pad_string_and_wrap_with_code "(${transpired_seconds}s)" "$time_color_code" 10
    printf "\n"
}

function pad_string_and_wrap_with_code {
    message="$1"
    color_code="$2"
    pad_to_length="$3"
    message_size=${#message}
    pad_length=$(( pad_to_length - message_size ))
    echo -en "$color_code"
    echo -en "$message$reset_code"
    printf %${pad_length}s
}

function _print_dots {
    initiation_message_size="$1"
    current_line_position=$(( initiation_message_size + 4 ))
    if [ $desired_dots_ending_column -gt $current_line_position ];
    then
        pad_size=$(( desired_dots_ending_column - current_line_position ))
    else
        pad_size=0
    fi
    padchar=$(echo -en "\u2508")
    count=0
    echo -en "$dots_color"
    while [[ "$count" != "$pad_size" ]];
    do
        echo -en "$padchar"
        count=$(( count + 1 ))
    done
    echo -en "$reset_code "
}


function print_dots {
    initiation_message_size=$(cat .initiation_message_size)
    current_line_position=$(( initiation_message_size + 4 ))
    rm .initiation_message_size
    if [ $desired_dots_ending_column -gt $current_line_position ];
    then
        pad_size=$(( desired_dots_ending_column - current_line_position ))
    else
        pad_size=0
    fi
    padchar=$(echo -en "\u2508")
    count=0
    echo -en "$dots_color"
    while [[ "$count" != "$pad_size" ]];
    do
        echo -en "$padchar"
        count=$(( count + 1 ))
    done
    echo -en "$reset_code "
}

function initialize_message_cache() {
    echo 'CREATE TABLE IF NOT EXISTS times(activity text, message text, started_time text, status_code int);' | sqlite3 buildcache.sqlite3
}

function message_start() {
    initialize_message_cache
    activity="$1"
    message="$2"
    started_time=$(date +%s)
    printf 'INSERT INTO times VALUES ("%s", "%s", "%s", "%s")' "$activity" "$message" "$started_time" "" | sqlite3 buildcache.sqlite3 >/dev/null
    display_initiation_message "$message"
}

function select_value_where() {
    field="$1"
    activity="$2"
    value=$(printf 'SELECT %s FROM times WHERE activity="%s";' "$field" "$activity" | sqlite3 buildcache.sqlite3)
    printf "$value"
}

function message_end() {
    activity="$1"
    on_completion_message="$2"
    on_error_message="$3"
    started_time=$(select_value_where started_time "$activity")
    message="$(select_value_where message "$activity")"
    status_code=$(select_value_where status_code "$activity")
    now_seconds=$(date +%s)
    transpired_seconds=$(( now_seconds - started_time ))
    if [[ "$status_code" != "0" ]];
    then
        display_error_message "$on_error_message" $transpired_seconds "$message"
    else
        display_completion_message "$on_completion_message" $transpired_seconds "$message"
    fi;
}

if [[ "$1" == "print" ]];
then
    echo "$2"
fi

if [[ "$1" == "start" ]];
then
    activity="$2"
    message="$3"

    # display_initiation_message "$2"
    # date +%s > .current_time.txt
    # message_length=$(echo -ne "$message" | tr -d '\n' | wc -m)
    # echo -n "$message_length" > .initiation_message_size

    message_start "$activity" "$message"
fi

if [[ "$1" == "end" ]];
then
    # status_code=$(cat status_code)
    # on_completion_message="$2"
    # on_error_message="$3"
    # initial=$(cat .current_time.txt)
    # rm .current_time.txt
    # now_seconds=$(date +%s)
    # transpired_seconds=$(( now_seconds - initial ))
    # print_dots
    # if [ $status_code -gt 0 ];
    # then
    #     display_error_message "$on_error_message" $transpired_seconds
    # else
    #     display_completion_message "$on_completion_message" $transpired_seconds
    # fi
    # echo ''

    message_end "$2" "$3" "$4"
fi
