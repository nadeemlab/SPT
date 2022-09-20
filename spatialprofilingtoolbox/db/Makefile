
build-dockerfile: initialize_schema.sql
	@echo > /dev/null

initialize_schema.sql: data_model/schema.sql
	@cat\
    data_model/schema.sql \
    data_model/performance_tweaks.sql \
    data_model/create_views.sql \
    > initialize_schema.sql

data_model/schema.sql:
	@${PYTHON} -m venv venv ; \
    source venv/bin/activate ; \
    ${PYTHON} -m pip install adisinglecell >/dev/null 2>&1 ; \
    adisinglecell dump-schema > data_model/schema.sql ; \
    deactivate ; \
    rm -rf venv/

unit-tests:
	@docker compose up & >/dev/null 2>&1
	@${PYTHON} -m venv venv
	@source venv/bin/activate ; \
    ${PYTHON} -m pip install "../../dist/${WHEEL_FILENAME}[db]" >/dev/null 2>&1 ; \
    for test_script in $$(find unit_tests/test_* | grep \.sh$$ ); \
    do \
        test_name=$${test_script/unit_tests\/test_/}; \
        test_name=$${test_name/.sh/}; \
        test_name=$${test_name/_/ }; \
        "${MESSAGE}" start "Testing $$test_name" ; \
        bash $$test_script >/dev/null 2>&1 ; \
	    "${MESSAGE}" end "$$?" "Passed." "Failed." ; \
    done ; \
    deactivate
	@docker compose down 
	@rm -rf venv/

module-tests:
	@echo 'Module tests.'

clean:
	@rm -f ${WHEEL_FILENAME}
	@rm -f initialize_schema.sql
	@rm -rf venv/
	@rm -f data_model/schema.sql
