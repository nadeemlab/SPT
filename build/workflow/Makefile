.RECIPEPREFIX = >

MODULE_NAME := $(shell echo "verbose-shell-override" >/dev/null ; pwd | grep -o '[^/]\+$$' )

UNIT_TEST_FILES := $(wildcard ../../${TEST_LOCATION}/${MODULE_NAME}/unit_tests/test_*.sh ) $(wildcard ../../${TEST_LOCATION}/${MODULE_NAME}/unit_tests/test_*.py )
UNIT_TESTS := $(foreach test_file,$(UNIT_TEST_FILES),test-$(test_file))

MODULE_TEST_FILES := $(wildcard ../../${TEST_LOCATION}/${MODULE_NAME}/module_tests/test_*.sh ) $(wildcard ../../${TEST_LOCATION}/${MODULE_NAME}/module_tests/test_*.py )
MODULE_TESTS := $(foreach test_file,$(MODULE_TEST_FILES),test-$(test_file))
TESTS := ${UNIT_TESTS} ${MODULE_TESTS}

STANDALONE_MODULE_TEST_CONFIGURATION_SCRIPT := ${MODULE_NAME}/module_tests/configure_graph_plugin_test.sh
STANDALONE_MODULE_TEST_FILE := ../../${TEST_LOCATION}/${MODULE_NAME}/module_tests/no_docker_test_graph_plugin.sh
STANDALONE_MODULE_TEST_TARGET := test-${STANDALONE_MODULE_TEST_FILE}
STANDALONE_MODULE_TEST_NAME := "graph-plugin-dockerized"

TEST_DIRECTORY := ../../${TEST_LOCATION}/${MODULE_NAME}
TD := ${TEST_DIRECTORY}
P := ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}

.PHONY: setup-testing teardown-unit-testing teardown-module-testing

unit-tests: teardown-unit-testing
module-tests: teardown-module-testing
combined-tests: teardown-testing

setup-testing:
>@rm -f buildcache.sqlite3
>@${MESSAGE} start "$@" "workflow"
>@docker compose up -d ; bash ${P}/record_docker_logs.sh & \
    LOG_PID=$$!; \
    echo 'CREATE TABLE IF NOT EXISTS log_pids(pid int);' | sqlite3 buildcache.sqlite3 ; \
    echo "INSERT INTO log_pids VALUES ($$LOG_PID);" | sqlite3 buildcache.sqlite3 ; \
    sleep 0.2 ; \
    bash ${P}/poll_container_readiness.sh \
     spt-db---testing-only-workflow; \
    status_code=$$? ; \
    printf 'UPDATE times SET status_code=%s WHERE activity="%s";' "$$status_code" "$@" | sqlite3 buildcache.sqlite3 ;
>@${MESSAGE} end "$@" "Setup env." "Env not setup."

teardown-unit-testing: ${UNIT_TESTS}
>@${MESSAGE} start "$@" "teardown workflow"
>@docker compose stop -t 1 && docker compose down && docker compose rm --force --stop ; status_code="$$?" ; \
    printf 'UPDATE times SET status_code=%s WHERE activity="%s";' "$$status_code" "$@" | sqlite3 buildcache.sqlite3 ;
>@rm -f ${TD}/nextflow.log; rm -f ${TD}/.nextflow.log*; rm -rf ${TD}/.nextflow/; rm -f ${TD}/configure.sh; rm -f ${TD}/run.sh; rm -f ${TD}/main.nf; rm -f ${TD}/nextflow.config; rm -rf ${TD}/work/; rm -rf ${TD}/results/
>@bash ${P}/print_docker_logs.sh
>@${MESSAGE} end "$@" "Down." "Error."

teardown-module-testing: ${MODULE_TESTS}
>@${MESSAGE} start "$@" "teardown workflow"
>@docker compose stop -t 1 && docker compose down && docker compose rm --force --stop ; status_code="$$?" ; \
    printf 'UPDATE times SET status_code=%s WHERE activity="%s";' "$$status_code" "$@" | sqlite3 buildcache.sqlite3 ;
>@rm -f ${TD}/nextflow.log; rm -f ${TD}/.nextflow.log*; rm -rf ${TD}/.nextflow/; rm -f ${TD}/configure.sh; rm -f ${TD}/run.sh; rm -f ${TD}/main.nf; rm -f ${TD}/nextflow.config; rm -rf ${TD}/work/; rm -rf ${TD}/results/
>@bash ${P}/print_docker_logs.sh
>@${MESSAGE} end "$@" "Down." "Error."

teardown-testing: ${TESTS}
>@${MESSAGE} start "$@" "teardown workflow"
>@docker compose stop -t 1 && docker compose down && docker compose rm --force --stop ; status_code="$$?" ; \
    printf 'UPDATE times SET status_code=%s WHERE activity="%s";' "$$status_code" "$@" | sqlite3 buildcache.sqlite3 ;
>@rm -f ${TD}/nextflow.log; rm -f ${TD}/.nextflow.log*; rm -rf ${TD}/.nextflow/; rm -f ${TD}/configure.sh; rm -f ${TD}/run.sh; rm -f ${TD}/main.nf; rm -f ${TD}/nextflow.config; rm -rf ${TD}/work/; rm -rf ${TD}/results/
>@bash ${P}/print_docker_logs.sh
>@${MESSAGE} end "$@" "Down." "Error."

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
    extension=$$(echo $$test_name | grep -o "\.sh\|\.py$$" ) ; \
    executor=none-cmd ; \
    if [[ "$$extension" == ".py" ]]; then executor=python; fi ; \
    if [[ "$$extension" == ".sh" ]]; then executor=bash; fi ; \
    test_cmd="cd /mount_sources/workflow/ && $$executor $$test_script"; \
    docker run \
     --rm \
     --network ${MODULE_NAME}_isolated_temporary_test \
     --mount type=bind,src=${TEST_LOCATION_ABSOLUTE},dst=/mount_sources \
     -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
     /bin/bash -c "$$test_cmd && exit $$?" ; \
    status_code=$$? ; \
    rm -f ${TD}/nextflow.log; rm -f ${TD}/.nextflow.log*; rm -rf ${TD}/.nextflow/; rm -f ${TD}/configure.sh; rm -f ${TD}/run.sh; rm -f ${TD}/main.nf; rm -f ${TD}/nextflow.config; rm -rf ${TD}/work/; rm -rf ${TD}/results/ ; \
    printf 'UPDATE times SET status_code=%s WHERE activity="%s";' "$$status_code" "$@" | sqlite3 buildcache.sqlite3 ;
>@${MESSAGE} end "$@" "Passed." "Failed."

${STANDALONE_MODULE_TEST_TARGET}: setup-testing
>@${MESSAGE} start "$@" "\u2503 ${STANDALONE_MODULE_TEST_NAME}"
>@docker run \
    --rm \
    --mount type=bind,src=${TEST_LOCATION_ABSOLUTE},dst=/mount_sources \
    -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
    /bin/bash -c "cd /mount_sources && bash ${STANDALONE_MODULE_TEST_CONFIGURATION_SCRIPT}"
>@bash ${STANDALONE_MODULE_TEST_FILE} ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest ; \
    status_code=$$? ; \
    printf 'UPDATE times SET status_code=%s WHERE activity="%s";' "$$status_code" "$@" | sqlite3 buildcache.sqlite3 ;
>@${MESSAGE} end "$@" "Passed." "Failed."

clean:
>@rm -f ${WHEEL_FILENAME}
>@rm -f ${TD}/nextflow.log; rm -f ${TD}/.nextflow.log*; rm -rf ${TD}/.nextflow/; rm -f ${TD}/configure.sh; rm -f ${TD}/run.sh; rm -f ${TD}/main.nf; rm -f ${TD}/nextflow.config; rm -rf ${TD}/work/; rm -rf ${TD}/results/
>@rm -f ${TD}/plots.html
>@for f in dlogs.db.txt dlogs.api.txt dlogs.od.txt; do rm -f $$f; done;
>@rm -f buildcache.sqlite3
