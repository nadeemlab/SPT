
function consider_exit() {
    if [[ "$1" != "0" ]];
    then
        exit 1
    fi
}

spt db index-expressions-table --database-config-file .spt_db.config.container
status=$?; consider_exit $status

spt db index-expressions-table --database-config-file .spt_db.config.container
status=$?; consider_exit $status

spt db index-expressions-table --database-config-file .spt_db.config.container --drop-index
status=$?; consider_exit $status
