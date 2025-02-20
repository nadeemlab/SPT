.RECIPEPREFIX = >

MODULE_NAME := $(shell echo "verbose-shell-override" >/dev/null ; pwd | grep -o '[^/]\+$$' )

UNIT_TEST_FILES := $(wildcard ../../${TEST_LOCATION}/${MODULE_NAME}/unit_tests/test_*.sh ) $(wildcard ../../${TEST_LOCATION}/${MODULE_NAME}/unit_tests/test_*.py )
UNIT_TESTS := $(foreach test_file,$(UNIT_TEST_FILES),test-$(test_file))

MODULE_TEST_FILES := $(wildcard ../../${TEST_LOCATION}/${MODULE_NAME}/module_tests/test_*.sh ) $(wildcard ../../${TEST_LOCATION}/${MODULE_NAME}/module_tests/test_*.py )
MODULE_TESTS := $(foreach test_file,$(MODULE_TEST_FILES),test-$(test_file))

TESTS := ${UNIT_TESTS} ${MODULE_TESTS}

P := ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}

.PHONY: setup-testing teardown-unit-testing teardown-module-testing

unit-tests: teardown-unit-testing
module-tests: teardown-module-testing

setup-testing:
>@rm -f buildcache.sqlite3
>@${MESSAGE} start "$@" "ondemand"
>@docker compose up -d && (bash ${P}/record_docker_logs.sh &) && sleep 0.2 && \
    bash ${P}/poll_container_readiness.sh \
     spt-ondemand--testing-ondemand \
     spt-db---testing-only-ondemand ; \
    status_code=$$? ; \
    printf 'UPDATE times SET status_code=%s WHERE activity="%s";' "$$status_code" "$@" | sqlite3 buildcache.sqlite3 ;
>@${MESSAGE} end "$@" "Setup env." "Env not setup."

teardown-unit-testing: ${UNIT_TESTS}
>@${MESSAGE} start "$@" "teardown ondemand"
>@docker compose down && docker compose rm --force --stop ; status_code="$$?" ; \
    printf 'UPDATE times SET status_code=%s WHERE activity="%s";' "$$status_code" "$@" | sqlite3 buildcache.sqlite3 ;
>@bash ${P}/print_docker_logs.sh
>@${MESSAGE} end "$@" "Down." "Error."
>@rm -f ${TEST_LOCATION_ABSOLUTE}/ondemand/test_expression_data/.spt_db.config.generated

teardown-module-testing: ${MODULE_TESTS}
>@${MESSAGE} start "$@" "teardown ondemand"
>@docker compose down && docker compose rm --force --stop ; status_code="$$?" ; \
    printf 'UPDATE times SET status_code=%s WHERE activity="%s";' "$$status_code" "$@" | sqlite3 buildcache.sqlite3 ;
>@bash ${P}/print_docker_logs.sh
>@${MESSAGE} end "$@" "Down." "Error."
>@rm -f ${TEST_LOCATION_ABSOLUTE}/ondemand/test_expression_data/.spt_db.config.generated

${TESTS}: setup-testing
>@test_target=$$(echo $@ | sed 's/..\/..\/${TEST_LOCATION}\/${MODULE_NAME}\///g') ; \
    test_script=$${test_target/test-/} ; \
    test_name=$${test_script/module_tests\/test_/} ; \
    test_name=$${test_name/unit_tests\/test_/} ; \
    extension=$$(echo $$test_name | grep -o "\.sh\|\.py$$" ) ; \
    test_name=$${test_name/$$extension/} ; \
    test_name=$$(echo "$$test_name" | tr '_' ' ' ) ; \
    ${MESSAGE} start "$@" "$$test_name"
>@test_target=$$(echo $@ | sed 's/..\/..\/${TEST_LOCATION}\/${MODULE_NAME}\///g') ; \
    test_script=$${test_target/test-/} ; \
    test_name=$${test_script/module_tests\/test_/} ; \
    test_name=$${test_name/unit_tests\/test_/} ; \
    extension=$$(echo $$test_name | grep -o "\.sh\|\.py$$" ) ; \
    executor=none-cmd ; \
    if [[ "$$extension" == ".py" ]]; then executor=${PYTHON}; fi ; \
    if [[ "$$extension" == ".sh" ]]; then executor=bash; fi ; \
    test_cmd="cd /mount_sources/ondemand/ && SINGLE_CELL_DATABASE_HOST=spt-db---testing-only-ondemand SINGLE_CELL_DATABASE_USER=postgres SINGLE_CELL_DATABASE_PASSWORD=postgres USE_ALTERNATIVE_TESTING_DATABASE=1 $$executor $$test_script" ; \
    docker run \
     --rm \
     --network ${MODULE_NAME}_isolated_temporary_test \
     --mount type=bind,src=${TEST_LOCATION_ABSOLUTE},dst=/mount_sources \
     -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
     /bin/bash -c "$$test_cmd && exit $$?" ; \
    status_code=$$? ; \
    printf 'UPDATE times SET status_code=%s WHERE activity="%s";' "$$status_code" "$@" | sqlite3 buildcache.sqlite3 ;
>@${MESSAGE} end "$@" "Passed." "Failed."

clean:
>@rm -f ${WHEEL_FILENAME}
>@rm -rf ../../test/ondemand/expression_data/
>@rm -rf ../../test/test_data/fast_cache_testing
