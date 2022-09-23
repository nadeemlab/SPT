
spt db create-schema --database-config-file .spt_db.config.local --force >/dev/null 2>err_log.1.txt
spt db modify-constraints --database-config-file .spt_db.config.local --drop >/dev/null 2>err_log.2.txt
spt db modify-constraints --database-config-file .spt_db.config.local --recreate > constraint_info.txt.comp 2>err_log.3.txt
diff module_tests/constraint_info.txt constraint_info.txt.comp >/dev/null
status=$?
[ $status -eq 0 ] || echo "Drop/recreate FAILED."
rm constraint_info.txt.comp

if [ $status -eq 0 ];
then
    rm err_log.1.txt err_log.2.txt err_log.3.txt
    exit 0
else
    cat err_log.1.txt err_log.2.txt err_log.3.txt
    rm err_log.1.txt err_log.2.txt err_log.3.txt
    exit 1
fi
