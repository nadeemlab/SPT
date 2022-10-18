.RECIPEPREFIX = >

UNIT_TEST_FILES := $(wildcard unit_tests/test_*.sh ) $(wildcard unit_tests/test_*.py )
UNIT_TESTS := $(foreach test_file,$(UNIT_TEST_FILES),test-$(test_file))

MODULE_TEST_FILES := $(wildcard module_tests/test_*.sh ) $(wildcard module_tests/test_*.py )
MODULE_TESTS := $(foreach test_file,$(MODULE_TEST_FILES),test-$(test_file))

TESTS := ${UNIT_TESTS} ${MODULE_TESTS}

build-dockerfile: initialize_schema.sql
>@touch build-dockerfile

initialize_schema.sql: data_model/schema.sql
>@cat \
    data_model/schema.sql \
    data_model/performance_tweaks.sql \
    data_model/create_views.sql \
    > initialize_schema.sql

data_model/schema.sql:
>@docker run \
     --rm \
     --mount type=bind,src=${DB_DIRECTORY},dst=/mount_sources \
     -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
     /bin/bash -c \
     'cd /mount_sources; adisinglecell dump-schema > schema.sql' && \
     mv schema.sql data_model/ ; \
     echo "$$?" > status_code

.PHONY: setup-testing teardown-unit-testing teardown-module-testing teardown-testing

unit-tests: teardown-unit-testing
module-tests: teardown-module-testing
test: teardown-testing

setup-testing:
>@docker compose up -d && \
    bash ../../building/poll_container_readiness.sh \
     spt-db-testing

teardown-unit-testing: ${UNIT_TESTS}
>@docker compose rm --force --stop

teardown-module-testing: ${MODULE_TESTS}
>@docker compose rm --force --stop

teardown-testing: ${TESTS}
>@docker compose rm --force --stop

${TESTS}: setup-testing
>@test_target=$@ ; \
    test_script=$${test_target/test-/} ; \
    test_name=$${test_script/module_tests\/test_/} ; \
    test_name=$${test_name/unit_tests\/test_/} ; \
    extension=$$(echo $$test_name | grep -o "\.sh\|\.py$$" ) ; \
    test_name=$${test_name/$$extension/} ; \
    test_name=$$(echo "$$test_name" | tr '_' ' ' ) ; \
    ${MESSAGE} start "Testing $$test_name"
>@test_target=$@ ; \
    test_script=$${test_target/test-/} ; \
    test_name=$${test_script/module_tests\/test_/} ; \
    test_name=$${test_name/unit_tests\/test_/} ; \
    extension=$$(echo $$test_name | grep -o "\.sh\|\.py$$" ) ; \
    executor=none-cmd ; \
    if [[ "$$extension" == ".py" ]]; then executor=python; fi ; \
    if [[ "$$extension" == ".sh" ]]; then executor=bash; fi ; \
    test_cmd="cd /mount_sources/db/; $$executor $$test_script" ; \
    docker run \
     --rm \
     --network host \
     --mount type=bind,src=${PACKAGE_DIRECTORY},dst=/mount_sources \
     -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
     /bin/bash -c "$$test_cmd" ; \
    echo "$$?" > status_code
>@${MESSAGE} end "Passed." "Failed."
>@rm -f status_code

clean:
>@rm -f ${WHEEL_FILENAME}
>@rm -f initialize_schema.sql
>@rm -f data_model/schema.sql
>@rm -f status_code
>@rm -f err_log.*.txt
>@rm -rf requirements.txt
>@rm -rf specific_requirements.txt
>@rm -f build-dockerfile
