
titlecolor="\033[35;1m"
reset_code="\033[0m"

echo
echo -e "${titlecolor}Docker compose logs:${reset_code}"
for f in dlogs.db.txt dlogs.api.txt dlogs.od.txt dlogs.od2.txt;
do
    cat $f
    rm $f
done

echo

kernel_name=$(uname -s)
if [[ "$kernel_name" == "Linux" ]];
then
    for p in $(echo "SELECT pid FROM log_pids;" | sqlite3 buildcache.sqlite3);
    do
        kill -9 "$p"
    done;
fi;
echo 'DELETE FROM log_pids;' | sqlite3 buildcache.sqlite3;
