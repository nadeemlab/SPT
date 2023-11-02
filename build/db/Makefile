.RECIPEPREFIX = >

MODULE_NAME := $(shell echo "verbose-shell-override" >/dev/null ; pwd | grep -o '[^/]\+$$' )

SINGLETON_TEST_FILES := ../../${TEST_LOCATION}/${MODULE_NAME}/singleton_tests/test_study_dropping.sh
SINGLETON_TESTS := $(foreach test_file,$(SINGLETON_TEST_FILES),test-$(test_file))

UNIT_TEST_FILES := $(wildcard ../../${TEST_LOCATION}/${MODULE_NAME}/unit_tests/test_*.sh ) $(wildcard ../../${TEST_LOCATION}/${MODULE_NAME}/unit_tests/test_*.py )
UNIT_TESTS := $(foreach test_file,$(UNIT_TEST_FILES),test-$(test_file))

MODULE_TEST_FILES := $(wildcard ../../${TEST_LOCATION}/${MODULE_NAME}/module_tests/test_*.sh ) $(wildcard ../../${TEST_LOCATION}/${MODULE_NAME}/module_tests/test_*.py )
MODULE_TESTS := $(foreach test_file,$(MODULE_TEST_FILES),test-$(test_file))

TESTS := ${UNIT_TESTS} ${MODULE_TESTS} ${SINGLETON_TESTS}

DATA_MODEL_SOURCE_LOCATION := ${DB_SOURCE_LOCATION_ABSOLUTE}/data_model

schema.sql:
>@docker run \
     --rm \
     --mount type=bind,src=${DB_BUILD_LOCATION_ABSOLUTE},dst=/mount_sources \
     -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
     /bin/bash -c \
     'cd /mount_sources; adiscstudies dump-schema > schema.sql' ; \
     echo "$$?" > status_code

.PHONY: setup-testing teardown-unit-testing teardown-module-testing teardown-testing

singleton-tests: teardown-singleton-testing
unit-tests: teardown-unit-testing
module-tests: teardown-module-testing
test: teardown-testing

setup-testing:
>@${MESSAGE} start "db"
>@docker compose up -d && \
    bash ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/poll_container_readiness.sh \
     spt-db-testing-only ; \
    echo "$$?" > status_code
>@${MESSAGE} end "Setup env." "Env not setup."
>@rm -f status_code

teardown-singleton-testing: ${SINGLETON_TESTS}
>@${MESSAGE} start "\u2517\u2501"
>@docker compose down && docker compose rm --force --stop ; echo "$$?" > status_code
>@${MESSAGE} end "Down." "Error."
>@rm -f status_code

teardown-unit-testing: ${UNIT_TESTS}
>@${MESSAGE} start "\u2517\u2501"
>@docker compose down && docker compose rm --force --stop ; echo "$$?" > status_code
>@${MESSAGE} end "Down." "Error."
>@rm -f status_code

teardown-module-testing: ${MODULE_TESTS}
>@${MESSAGE} start "\u2517\u2501"
>@docker compose down && docker compose rm --force --stop ; echo "$$?" > status_code
>@${MESSAGE} end "Down." "Error."

teardown-testing: ${TESTS}
>@${MESSAGE} start "\u2517\u2501"
>@docker compose down && docker compose rm --force --stop ; echo "$$?" > status_code
>@${MESSAGE} end "Down." "Error."
>@rm -f status_code

${TESTS}: setup-testing
>@test_target=$$(echo $@ | sed 's/..\/..\/${TEST_LOCATION}\/${MODULE_NAME}\///g') ; \
    test_script=$${test_target/test-/} ; \
    test_name=$${test_script/module_tests\/test_/} ; \
    test_name=$${test_name/unit_tests\/test_/} ; \
    extension=$$(echo $$test_name | grep -o "\.sh\|\.py$$" ) ; \
    test_name=$${test_name/$$extension/} ; \
    test_name=$$(echo "$$test_name" | tr '_' ' ' ) ; \
    ${MESSAGE} start "\u2503 $$test_name"
>@test_target=$$(echo $@ | sed 's/..\/..\/${TEST_LOCATION}\/${MODULE_NAME}\///g') ; \
    test_script=$${test_target/test-/} ; \
    test_name=$${test_script/module_tests\/test_/} ; \
    test_name=$${test_name/unit_tests\/test_/} ; \
    extension=$$(echo $$test_name | grep -o "\.sh\|\.py$$" ) ; \
    executor=none-cmd ; \
    if [[ "$$extension" == ".py" ]]; then executor=python; fi ; \
    if [[ "$$extension" == ".sh" ]]; then executor=bash; fi ; \
    test_cmd="cd /mount_sources/db/; $$executor $$test_script" ; \
    bash ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/record_docker_logs.sh & \
    sleep 0.2; \
    docker run \
     --rm \
     --network ${MODULE_NAME}_isolated_temporary_test \
     --mount type=bind,src=${TEST_LOCATION_ABSOLUTE},dst=/mount_sources \
     -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
     /bin/bash -c "$$test_cmd"; \
    echo "$$?" > status_code ; \
    kill %1
>@bash ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/print_docker_logs.sh
>@${MESSAGE} end "Passed." "Failed."
>@rm -f status_code

clean:
>@rm -f ${WHEEL_FILENAME}
>@rm -rf schema.sql
>@rm -f status_code
>@rm -f err_log.*.txt
>@for f in dlogs.db.txt dlogs.api.txt dlogs.od.txt; do rm -f $$f; done;
