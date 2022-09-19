
build-dockerfile: initialize_schema.sql
	@echo > /dev/null

initialize_schema.sql: data_model/schema.sql
	@cat\
    data_model/schema.sql \
    data_model/performance_tweaks.sql \
    data_model/create_views.sql \
    data_model/grant_on_tables.sql \
    > initialize_schema.sql

data_model/schema.sql:
	@python -m venv venv ; \
    source venv/bin/activate ; \
    python -m pip install adisinglecell >/dev/null 2>&1 ; \
    adisinglecell dump-schema > data_model/schema.sql ; \
    deactivate ; \
    rm -rf venv/

clean:
	@rm -f ${WHEEL_FILENAME}
	@rm -f initialize_schema.sql
	@rm -rf venv/
	@rm -f data_model/schema.sql
