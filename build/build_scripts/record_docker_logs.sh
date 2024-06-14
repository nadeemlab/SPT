
titlecolor="\033[35;1m"
reset_code="\033[0m"

echo
echo
echo -e "${titlecolor}(Started recording Docker compose logs for this test.)${reset_code}"

nowtime=$(TZ=GMT date -u +"%Y-%m-%dT%H:%M:%SZ") ; \
unbuffer docker compose logs --since="$nowtime" -f testing-database > dlogs.db.txt &
unbuffer docker compose logs --since="$nowtime" -f testing-api-server > dlogs.api.txt &
unbuffer docker compose logs --since="$nowtime" -f testing-fast-counts-server > dlogs.od.txt &
unbuffer docker compose logs --since="$nowtime" -f testing-fast-counts-server2 > dlogs.od2.txt &
tail -f /dev/null
