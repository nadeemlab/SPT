
python module_tests/sqlite_dump.py
ls -lrta dump_*.db
for size in $(ls -lrta dump_*.db | awk '{print $5}');
do
    if [ $size -ge 10000 ];
    then
        echo $size bytes
    else
        echo "SQLite database dump size too low: $size"
        exit 1
    fi;
done
rm dump_*.db
