
titlecolor="\033[35;1m"
reset_code="\033[0m"

echo
echo -e "${titlecolor}Docker compose logs:${reset_code}"
for f in dlogs.db.txt dlogs.api.txt dlogs.od.txt dlogs.od2.txt;
do
    cat $f
    rm $f
done

rm dlogs.db.txt

echo
