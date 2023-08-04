
nowtime=$(TZ=GMT date -u +"%Y-%m-%dT%H:%M:%SZ") ; \
unbuffer docker compose logs --since="$nowtime" -f testing-database > dlogs.db.txt &
unbuffer docker compose logs --since="$nowtime" -f testing-api-server > dlogs.api.txt &
unbuffer docker compose logs --since="$nowtime" -f testing-fast-counts-server > dlogs.od.txt&
tail -f /dev/null
