
function main() {
    runs_directory="$1"
    base=$(get_base "$runs_directory")
    if [[ "$base" != "umap_runs" ]];
    then
        echo "Error: The run directory you supplied does not end in 'umap_runs'."
        exit 1
    fi
    if [[ -d "$runs_directory" ]];
    then
        rm -rf "$runs_directory"
    fi
    mkdir "$runs_directory"
    echo "Created directory $runs_directory"
    db_config_file="$2"
    configure_all_umaps "$runs_directory" "$db_config_file"
    run_all_umaps "$runs_directory"
}

function get_base() {
    set -- "${1%"${1##*[!/]}"}"
    printf '%s\n' "${1##*/}"
}

function configure_all_umaps() {
    runs_directory="$1"
    db_config_file="$2"
    while read -r study_name
    do
        configure_umaps_one_dataset "$runs_directory" "$db_config_file" "$study_name"
        if [[ "$?" != "0" ]];
        then
            echo "Failed to configure '$study_name' UMAPs workflow."
            exit 1
        fi
    done < <(fetch_study_names)
}

function fetch_study_names() {
    spt db list-studies --database-config-file="$db_config_file"
}

function configure_umaps_one_dataset() {
    runs_directory="$1"
    db_config_file="$2"
    study_name="$3"
    echo "Doing UMAPs workflow configuration for '$study_name'."
    noted_pwd="$PWD"
    sanitized=$(echo "$study_name" | sed 's/ /_/g')
    workflow_directory="$PWD/$runs_directory/$sanitized"
    if [[ -d "$workflow_directory" ]]
    then
        rm -rf "$workflow_directory"
    fi
    mkdir "$workflow_directory"
    cd "$workflow_directory"

    echo "[general]" >> workflow.config
    echo "db_config_file = $db_config_file" >> workflow.config
    echo "" >> workflow.config
    echo "[database visitor]" >> workflow.config
    echo "study_name = $study_name" >> workflow.config
    echo "" >> workflow.config

    spt workflow configure --workflow="reduction visual" --config-file=workflow.config
    cd "$noted_pwd"
}

function run_all_umaps() {
    runs_directory="$1"
    while read -r run_directory
    do
        run_umaps_one_dataset "$run_directory"
    done < <(fetch_run_directories "$runs_directory")
}

function fetch_run_directories() {
    runs_directory="$1"
    find $runs_directory -maxdepth 1 -mindepth 1
}

function run_umaps_one_dataset() {
    run_directory="$1"
    echo ""
    echo "Doing UMAPs workflow in $run_directory ."
    noted_pwd="$PWD"
    cd $run_directory
    ./run.sh
    status="$?"
    cd "$noted_pwd"
    if [[ "$status" != "0" ]];
    then
        echo "UMAPs workflow in '$run_directory' failed."
    fi
}

main "$1" "$2"
