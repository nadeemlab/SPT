
CREATE ROLE apireader WITH LOGIN;
\password apireader
# input

# Refactor this into a template, so usable programmatically

CREATE ROLE nadeemlab WITH LOGIN;
\password nadeemlab
# input

GRANT CONNECT ON DATABASE pathstudies TO apireader;
GRANT USAGE ON SCHEMA public TO apireader;

GRANT CONNECT ON DATABASE pathstudies TO nadeemlab;
GRANT USAGE ON SCHEMA public TO nadeemlab;
