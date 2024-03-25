#!/bin/bash

name="SPT application monitor"
declare -A pane
pane["kubectl get pods"]="0"
pane["Memory and CPU"]="1"
pane["API service"]="2"
pane["Counts service"]="3"
pane["Proximity metrics service"]="4"
pane["Squidpy metrics service"]="5"
pane["Frontend nginx"]="6"
_ingress_pod_panes=(7 8 9)

function setup_and_split_panes() {
    tmux kill-session -t "$name"
    tmux new-session -s "$name" \; detach

    tmux split-window -v -t 0
    tmux split-window -v -t 0
    tmux split-window -v -t 0
    tmux split-window -v -t 0

    tmux select-layout -t "$name" even-vertical

    tmux split-window -h -t 0
    tmux split-window -h -t 2
    tmux split-window -h -t 4
    tmux split-window -v -t 6
    tmux split-window -v -t 8
}

function get_pod_names() {
    export api_pod=$(kubectl get pods | grep 'spt-api-' | cut -f1 -d' ')
    export counts_pod=$(kubectl get pods | grep 'spt-fast-counts-\|spt-counts' | cut -f1 -d' ')
    export proximity_pod=$(kubectl get pods | grep 'spt-proximity-' | cut -f1 -d' ')
    export squidpy_pod=$(kubectl get pods | grep 'spt-squidpy-' | cut -f1 -d' ')
    export frontend_pod=$(kubectl get pods | grep 'spt-frontend-' | cut -f1 -d' ')
    export ingress_pods=$(kubectl get pods -n ingress-nginx | tail -n3 | cut -f1 -d' ')
    export _ingress_pods=($ingress_pods)
}

function set_titles() {
    for key in "${!pane[@]}"
    do
        tmux select-pane -t "${pane[${key}]}" -T "$key"
    done

    for i in "${!_ingress_pods[@]}"
    do
        tmux select-pane -t ${_ingress_pod_panes[i]} -T "${_ingress_pods[i]}"
    done
}

function clear_panes() {
    for f in $(seq 0 9)
    do
        tmux send-keys -t $f 'clear' Enter
    done
}

function run_initial_commands_in_panes() {
    tmux send-keys -t "${pane['kubectl get pods']}" 'bash scripts/_get_pods.sh' Enter
    tmux send-keys -t "${pane['Memory and CPU']}" "bash scripts/_top_pod.sh" Enter
    tmux send-keys -t "${pane['Counts service']}" "kubectl logs $counts_pod -f" Enter
    tmux send-keys -t "${pane['Frontend nginx']}" "kubectl logs $frontend_pod -f" Enter
    tmux send-keys -t "${pane['API service']}" "kubectl logs $api_pod -f" Enter
    tmux send-keys -t "${pane['Proximity metrics service']}" "kubectl logs $proximity_pod -f" Enter
    tmux send-keys -t "${pane['Squidpy metrics service']}" "kubectl logs $squidpy_pod -f" Enter

    _COLUMNS=$(tput cols)
    for i in "${!_ingress_pods[@]}"
    do
        tmux send-keys -t ${_ingress_pod_panes[i]} "kubectl logs -n ingress-nginx ${_ingress_pods[i]} -f | cut -c1-${_COLUMNS}" Enter
    done
}

function configure_tmux() {
    tmux set -g window-status-current-format "#[fg=#569CD6] "
    tmux setw -g automatic-rename off
    tmux set-option -t "$name" status-format " #S "
    tmux set -g pane-border-status top
    tmux set -g pane-border-format " #T "
}

function start_monitor() {
    echo "Starting $name."
    sleep 1
    tmux attach-session -t "$name"
}

setup_and_split_panes
get_pod_names
set_titles
clear_panes
run_initial_commands_in_panes
configure_tmux
start_monitor
