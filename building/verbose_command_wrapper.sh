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
    echo -n "$1 "
    echo -en "$reset_code$dots_color""...""$reset_code"
}

function display_completion_message() {
    pad_string_and_wrap_with_code "$1" "$completion_color_code" $status_message_size_limit
    display_transpired_seconds $2
}

function display_error_message() {
    pad_string_and_wrap_with_code "$1" "$error_color_code" $status_message_size_limit
    display_transpired_seconds $2
}

function display_transpired_seconds() {
    transpired_seconds=$1
    pad_string_and_wrap_with_code "(${transpired_seconds}s)" "$time_color_code" 10
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
    dots_bar=$(printf %${pad_size}s |tr " " ".")
    echo -en "$dots_color$dots_bar$reset_code "
}

if [[ "$1" == "start" ]];
then
    message="$2"
    display_initiation_message "$2"
    date +%s > .current_time.txt
    echo -n "${#message}" > .initiation_message_size
fi

if [[ "$1" == "end" ]];
then
    status_code=$(cat status_code)
    on_completion_message="$2"
    on_error_message="$3"
    initial=$(cat .current_time.txt)
    rm .current_time.txt
    now_seconds=$(date +%s)
    transpired_seconds=$(( now_seconds - initial ))
    print_dots
    if [ $status_code -gt 0 ];
    then
        display_error_message "$on_error_message" $transpired_seconds
    else
        display_completion_message "$on_completion_message" $transpired_seconds
    fi
    echo ''
fi
