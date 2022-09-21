
spt db create-schema --database-config-file= .spt_db.config.local --force
spt db modify-constraints --database-config-file .spt_db.config.local --drop
spt db modify-constraints --database-config-file .spt_db.config.local --recreate > constraint_info.txt.comp
diff module_tests/constraint_info.txt constraint_info.txt.comp
status=$?
[ $status -eq 0 ] && echo "Drop/recreate succeeded." || echo "Drop/recreate FAILED."
rm constraint_info.txt.comp

if [ $status -eq 0 ];
then
    exit 0
else
    exit 1
fi
