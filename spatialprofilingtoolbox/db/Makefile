
build-dockerfile: initialize_schema.sql
	@echo > /dev/null

initialize_schema.sql: data_model/schema.sql
	@cat\
    data_model/schema.sql \
    data_model/performance_tweaks.sql \
    data_model/create_views.sql \
    > initialize_schema.sql

data_model/schema.sql:
	@source ../../venvs/db/bin/activate ; \
    adisinglecell dump-schema > data_model/schema.sql ; \
    deactivate ; \

unit-tests:
	@docker compose up -d >/dev/null 2>&1
	@sleep 1s
	@source ../../venvs/db/bin/activate ; \
    for test_script in $$(find unit_tests/test_* | grep \.sh$$ ); \
    do \
        test_name=$${test_script/unit_tests\/test_/}; \
        test_name=$${test_name/.sh/}; \
        test_name=$$(echo "$$test_name" | tr '_' ' ' ); \
        "${MESSAGE}" start "Testing $$test_name" ; \
        bash $$test_script >/dev/null 2>&1 ; \
        "${MESSAGE}" end "$$?" "Passed." "Failed." ; \
    done ; \
    deactivate
	@docker compose down >/dev/null 2>&1

module-tests:
	@echo 'Module tests.'

clean:
	@rm -f ${WHEEL_FILENAME}
	@rm -f initialize_schema.sql
	@rm -f data_model/schema.sql
