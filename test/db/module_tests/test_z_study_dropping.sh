
spt db status --database-config-file .spt_db.config.container > current_counts.txt;
diff current_counts.txt module_tests/record_counts_1_2.txt
status="$?"
rm current_counts.txt
if [[ "$status" != "0" ]];
then
    echo "Wrong of records to begin with in this test."
    exit 1
fi

spt db drop --study-name="Melanoma intralesional IL2"  --database-config-file .spt_db.config.container
spt db status --database-config-file .spt_db.config.container > counts_after_drop.txt;

diff counts_after_drop.txt module_tests/record_counts_1_2.txt
if [[ "$?" != "0" ]];
then
    echo "Wrong number of counts after dropping. (JK)"
    cat counts_after_drop.txt
    rm counts_after_drop.txt
    exit 1
fi
rm counts_after_drop.txt
