spt db modify-constraints --database-config-file .spt_db.config.container --study "Melanoma intralesional IL2" --drop >/dev/null 2>err_log.2.txt
spt db modify-constraints --database-config-file .spt_db.config.container --study "Melanoma intralesional IL2" --recreate > constraint_info.txt.comp 2>err_log.3.txt
diff module_tests/constraint_info.txt constraint_info.txt.comp >/dev/null
status=$?
if [[ "$status" != "0" ]];
then
    echo "Drop/recreate FAILED."
    filename=module_tests/constraint_info.txt
    echo $filename ":"
    cat $filename
    echo ''
    filename=constraint_info.txt.comp
    echo $filename ":"
    cat $filename
    echo ''
fi
rm constraint_info.txt.comp

if [[ "$status" == "0" ]];
then
    rm err_log.2.txt err_log.3.txt
    exit 0
else
    echo "From drop..."
    cat err_log.2.txt
    echo ''
    echo "From recreate..."
    cat err_log.3.txt
    rm err_log.2.txt err_log.3.txt
    exit 1
fi
