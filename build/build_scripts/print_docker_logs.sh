
titlecolor="\033[35;1m"
reset_code="\033[0m"

echo
echo -e "${titlecolor}Docker compose logs:${reset_code}"
for f in dlogs.api.txt dlogs.od.txt;
do
    cat $f
    rm $f
done

rm dlogs.db.txt

echo