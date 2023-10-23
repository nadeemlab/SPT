.RECIPEPREFIX = >

MODULE_NAME := $(shell echo "verbose-shell-override" >/dev/null ; pwd | grep -o '[^/]\+$$' )

UNIT_TEST_FILES := $(wildcard ../../${TEST_LOCATION}/${MODULE_NAME}/unit_tests/test_*.sh ) $(wildcard ../../${TEST_LOCATION}/${MODULE_NAME}/unit_tests/test_*.py )
UNIT_TESTS := $(foreach test_file,$(UNIT_TEST_FILES),test-$(test_file))

MODULE_TEST_FILES := $(wildcard ../../${TEST_LOCATION}/${MODULE_NAME}/module_tests/test_*.sh ) $(wildcard ../../${TEST_LOCATION}/${MODULE_NAME}/module_tests/test_*.py )
MODULE_TESTS := $(foreach test_file,$(MODULE_TEST_FILES),test-$(test_file))
TESTS := ${UNIT_TESTS} ${MODULE_TESTS}

TEST_DIRECTORY := ../../${TEST_LOCATION}/${MODULE_NAME}
TD := ${TEST_DIRECTORY}

.PHONY: setup-testing teardown-unit-testing teardown-module-testing teardown-testing

unit-tests: teardown-unit-testing
module-tests: teardown-module-testing
test: teardown-testing

setup-testing:
>@${MESSAGE} start "workflow"
>@docker compose up -d && \
    bash ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/poll_container_readiness.sh \
     spt-db-testing; \
    echo "$$?" > status_code
>@${MESSAGE} end "Setup env." "Env not setup."
>@rm -f status_code

teardown-unit-testing: ${UNIT_TESTS}
>@${MESSAGE} start "\u2517\u2501"
>@docker compose down && docker compose rm --force --stop ; echo "$$?" > status_code
>@rm -f ${TD}/nextflow.log; rm -f ${TD}/.nextflow.log*; rm -rf ${TD}/.nextflow/; rm -f ${TD}/configure.sh; rm -f ${TD}/run.sh; rm -f ${TD}/main.nf; rm -f ${TD}/nextflow.config; rm -rf ${TD}/work/; rm -rf ${TD}/results/
>@${MESSAGE} end "Down." "Error."
>@rm -f status_code

teardown-module-testing: ${MODULE_TESTS}
>@${MESSAGE} start "\u2517\u2501"
>@docker compose down && docker compose rm --force --stop ; echo "$$?" > status_code
>@rm -f ${TD}/nextflow.log; rm -f ${TD}/.nextflow.log*; rm -rf ${TD}/.nextflow/; rm -f ${TD}/configure.sh; rm -f ${TD}/run.sh; rm -f ${TD}/main.nf; rm -f ${TD}/nextflow.config; rm -rf ${TD}/work/; rm -rf ${TD}/results/
>@${MESSAGE} end "Down." "Error."
>@rm -f status_code

teardown-testing: ${TESTS}
>@${MESSAGE} start "\u2517\u2501"
>@docker compose down && docker compose rm --force --stop ; echo "$$?" > status_code
>@rm -f ${TD}/nextflow.log; rm -f ${TD}/.nextflow.log*; rm -rf ${TD}/.nextflow/; rm -f ${TD}/configure.sh; rm -f ${TD}/run.sh; rm -f ${TD}/main.nf; rm -f ${TD}/nextflow.config; rm -rf ${TD}/work/; rm -rf ${TD}/results/
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
    extension=$$(echo $$test_name | grep -o "\.sh\|\.py$$" ) ; \
    executor=none-cmd ; \
    if [[ "$$extension" == ".py" ]]; then executor=python; fi ; \
    if [[ "$$extension" == ".sh" ]]; then executor=bash; fi ; \
    test_cmd="cd /mount_sources/workflow/; $$executor $$test_script" ; \
    bash ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/record_docker_logs.sh & \
    sleep 0.2; \
    docker run \
     --rm \
     --network ${MODULE_NAME}_isolated_temporary_test \
     --mount type=bind,src=${TEST_LOCATION_ABSOLUTE},dst=/mount_sources \
     -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
     /bin/bash -c "$$test_cmd" \
      --gpus all ; \
      echo "$$?" > status_code; \
    kill %1
>@bash ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/print_docker_logs.sh
>@${MESSAGE} end "Passed." "Failed."
>@rm -f status_code

clean:
>@rm -f ${WHEEL_FILENAME}
>@rm -f ${TD}/nextflow.log; rm -f ${TD}/.nextflow.log*; rm -rf ${TD}/.nextflow/; rm -f ${TD}/configure.sh; rm -f ${TD}/run.sh; rm -f ${TD}/main.nf; rm -f ${TD}/nextflow.config; rm -rf ${TD}/work/; rm -rf ${TD}/results/
>@rm -f status_code
>@rm -f ${TD}/plots.html
>@for f in dlogs.db.txt dlogs.api.txt dlogs.od.txt; do rm -f $$f; done;
