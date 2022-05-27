
CREATE ROLE apireader WITH LOGIN;
\password apireader
# input

GRANT CONNECT ON DATABASE pathstudies TO apireader;
GRANT USAGE ON SCHEMA public TO apireader;
