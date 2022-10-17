.RECIPEPREFIX = >

UNIT_TEST_FILES := $(wildcard unit_tests/test_*.sh ) $(wildcard unit_tests/test_*.py )
UNIT_TESTS := $(foreach test_file,$(UNIT_TEST_FILES),test-$(test_file))

MODULE_TEST_FILES := $(wildcard module_tests/test_*.sh ) $(wildcard module_tests/test_*.py )
MODULE_TESTS := $(foreach test_file,$(MODULE_TEST_FILES),test-$(test_file))

build-dockerfile:
>@ echo >/dev/null

unit-tests: ${UNIT_TESTS}

${UNIT_TESTS}:
>@docker compose --project-directory ../db/ up -d
>@sleep 2s
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
    source ../../venvs/apiserver/bin/activate ; \
    $$executor $$test_script ; echo "$$?" > status_code ; \
    deactivate
>@${MESSAGE} end "Passed." "Failed."
>@docker compose --project-directory ../db/ rm --force --stop ; sleep 1s
>@rm -f status_code

.PHONY: setup-module-testing teardown-module-testing

module-tests: teardown-module-testing

setup-module-testing:
>@docker compose up -d && \
 bash ../../building/poll_container_readiness.sh \
  spt-apiserver-testing \
  spt-db-testing \
  spt-countsserver-testing
>@${MESSAGE} start "Populating temporary database with test data"
>@docker run \
     --rm \
     --network host \
     --mount type=bind,src=${PACKAGE_DIRECTORY},dst=/mount_sources \
     -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
     /bin/bash -c \
     'cd /mount_sources/workflow/; bash module_tests/test_HALO_exported_data_import.sh' ; \
    echo "$$?" > status_code
>@${MESSAGE} end "Populated." "Failed to populate."

${MODULE_TESTS}: setup-module-testing
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
    if [[ "$$extension" == ".py" ]]; then executor=python; fi ; \
    if [[ "$$extension" == ".sh" ]]; then executor=bash; fi ; \
    test_cmd="cd /mount_sources/apiserver/; $$executor $$test_script" ; \
    docker run \
     --rm \
     --network host \
     --mount type=bind,src=${PACKAGE_DIRECTORY},dst=/mount_sources \
     -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
     /bin/bash -c "$$test_cmd" ; \
    echo "$$?" > status_code
>@${MESSAGE} end "Passed." "Failed."
>@rm -f status_code

teardown-module-testing: ${MODULE_TESTS}
>@docker compose rm --force --stop

clean:
>@rm -f ${WHEEL_FILENAME}
>@rm -f status_code
>@rm -rf .nextflow/
>@rm -f .nextflow
>@rm -f .nextflow.*
>@rm -f nextflow.config
>@rm -f main.nf
>@rm -f configure.sh
>@rm -f run.sh
>@rm -rf work/
>@rm -rf results/
>@rm -rf requirements.txt
>@rm -rf specific_requirements.txt



