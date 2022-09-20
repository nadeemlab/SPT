
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
	@echo 'Unit tests.'

module-tests:
	@echo 'Module tests.'

clean:
	@rm -f ${WHEEL_FILENAME}
	@rm -f initialize_schema.sql
	@rm -rf venv/
	@rm -f data_model/schema.sql
