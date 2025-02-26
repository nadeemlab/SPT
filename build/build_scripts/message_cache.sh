
function initialize_message_cache() {
    echo 'CREATE TABLE IF NOT EXISTS times(activity text, message text, started_time text, status_code int);' | sqlite3 buildcache.sqlite3;
}
