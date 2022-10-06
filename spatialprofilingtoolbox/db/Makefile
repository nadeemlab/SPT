.RECIPEPREFIX = >

UNIT_TEST_FILES := $(wildcard unit_tests/test_*.sh ) $(wildcard unit_tests/test_*.py )
UNIT_TESTS := $(foreach test_file,$(UNIT_TEST_FILES),test-$(test_file))

MODULE_TEST_FILES := $(wildcard module_tests/test_*.sh ) $(wildcard module_tests/test_*.py )
MODULE_TESTS := $(foreach test_file,$(MODULE_TEST_FILES),test-$(test_file))

build-dockerfile: initialize_schema.sql
>@echo > /dev/null

initialize_schema.sql: data_model/schema.sql
>@cat \
    data_model/schema.sql \
    data_model/performance_tweaks.sql \
    data_model/create_views.sql \
    > initialize_schema.sql

data_model/schema.sql:
>@source ../../venvs/building/bin/activate ; \
    adisinglecell dump-schema > data_model/schema.sql ; \
    deactivate ; \

unit-tests: ${UNIT_TESTS}

${UNIT_TESTS}:
>@test_target=$@ ; \
    test_script=$${test_target/test-/} ; \
    test_name=$${test_script/unit_tests\/test_/} ; \
    extension=$$(echo $$test_name | grep -o "\.sh\|\.py$$" ) ; \
    test_name=$${test_name/$$extension/} ; \
    test_name=$$(echo "$$test_name" | tr '_' ' ' ) ; \
    ${MESSAGE} start "Testing $$test_name"
>@test_target=$@ ; \
    test_script=$${test_target/test-/} ; \
    test_name=$${test_script/unit_tests\/test_/} ; \
    extension=$$(echo $$test_name | grep -o "\.sh\|\.py$$" ) ; \
    executor=none-cmd ; \
    if [[ "$$extension" == ".py" ]]; then executor=${PYTHON}; fi ; \
    if [[ "$$extension" == ".sh" ]]; then executor=bash; fi ; \
    source ../../venvs/db/bin/activate ; \
    $$executor $$test_script ; echo "$$?" > status_code ; \
    deactivate
>@${MESSAGE} end "Passed." "Failed."
>@rm -f status_code

module-tests: ${MODULE_TESTS}

${MODULE_TESTS}:
>@docker compose up -d
>@sleep 1s
>@test_target=$@ ; \
    test_script=$${test_target/test-/} ; \
    test_name=$${test_script/module_tests\/test_/} ; \
    extension=$$(echo $$test_name | grep -o "\.sh\|\.py$$" ) ; \
    test_name=$${test_name/$$extension/} ; \
    test_name=$$(echo "$$test_name" | tr '_' ' ' ) ; \
    ${MESSAGE} start "Testing $$test_name"
>@test_target=$@ ; \
    test_script=$${test_target/test-/} ; \
    test_name=$${test_script/module_tests\/test_/} ; \
    extension=$$(echo $$test_name | grep -o "\.sh\|\.py$$" ) ; \
    executor=none-cmd ; \
    if [[ "$$extension" == ".py" ]]; then executor=${PYTHON}; fi ; \
    if [[ "$$extension" == ".sh" ]]; then executor=bash; fi ; \
    source ../../venvs/db/bin/activate ; \
    $$executor $$test_script ; echo "$$?" > status_code ; \
    deactivate
>@${MESSAGE} end "Passed." "Failed."
>@docker compose rm --force --stop ; sleep 1s
>@rm -f status_code

clean:
>@rm -f ${WHEEL_FILENAME}
>@rm -f initialize_schema.sql
>@rm -f data_model/schema.sql
>@rm -f status_code
>@rm -f err_log.*.txt
