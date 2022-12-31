.RECIPEPREFIX = >

MODULE_NAME := $(shell echo "verbose-shell-override" >/dev/null ; pwd | grep -o '[^/]\+$$' )

UNIT_TEST_FILES := $(wildcard unit_tests/test_*.sh ) $(wildcard unit_tests/test_*.py )
UNIT_TESTS := $(foreach test_file,$(UNIT_TEST_FILES),test-$(test_file))

MODULE_TEST_FILES := $(wildcard module_tests/test_*.sh ) $(wildcard module_tests/test_*.py )
MODULE_TESTS := $(foreach test_file,$(MODULE_TEST_FILES),test-$(test_file))

TESTS := ${UNIT_TESTS} ${MODULE_TESTS}

DATA_MODEL_SOURCE_DIRECTORY := ${DB_DIRECTORY}/data_model

Dockerfile: Dockerfile.template initialize_schema.sql
>@${MESSAGE} start "Building db Dockerfile"
>@cp Dockerfile.template Dockerfile ; echo "$$?" > status_code
>@${MESSAGE} end "Built." "Not built."
>@rm -f status_code

initialize_schema.sql: schema.sql ${DATA_MODEL_SOURCE_DIRECTORY}/performance_tweaks.sql ${DATA_MODEL_SOURCE_DIRECTORY}/create_views.sql
>@cat \
    schema.sql \
    ${DATA_MODEL_SOURCE_DIRECTORY}/performance_tweaks.sql \
    ${DATA_MODEL_SOURCE_DIRECTORY}/create_views.sql \
    > initialize_schema.sql

schema.sql:
>@docker run \
     --rm \
     --mount type=bind,src=${DB_BUILD_DIRECTORY},dst=/mount_sources \
     -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
     /bin/bash -c \
     'cd /mount_sources; adiscstudies dump-schema > schema.sql' ; \
     echo "$$?" > status_code

.PHONY: setup-testing teardown-unit-testing teardown-module-testing teardown-testing

unit-tests: teardown-unit-testing
module-tests: teardown-module-testing
test: teardown-testing

setup-testing:
>@${MESSAGE} start "db (setup testing environment)"
>@docker compose up -d && \
    bash ../../building/poll_container_readiness.sh \
     spt-db-testing ; \
    echo "$$?" > status_code
>@${MESSAGE} end "Setup." "Not setup."
>@rm -f status_code

teardown-unit-testing: ${UNIT_TESTS}
>@${MESSAGE} start "db (teardown testing environment)"
>@docker compose rm --force --stop ; echo "$$?" > status_code
>@${MESSAGE} end "Down." "Error."
>@rm -f status_code
>@rm -rf .nextflow/
>@rm -f .nextflow.log
>@rm -f .nextflow.log.*
>@rm -rf work/
>@rm -rf results/
>@rm -f main.nf
>@rm -f configure.sh
>@rm -f nextflow.config
>@rm -f run.sh

teardown-module-testing: ${MODULE_TESTS}
>@${MESSAGE} start "db (teardown testing environment)"
>@docker compose rm --force --stop ; echo "$$?" > status_code
>@${MESSAGE} end "Down." "Error."
>@rm -f status_code
>@rm -rf .nextflow/
>@rm -f .nextflow.log
>@rm -f .nextflow.log.*
>@rm -rf work/
>@rm -rf results/
>@rm -f main.nf
>@rm -f configure.sh
>@rm -f nextflow.config
>@rm -f run.sh

teardown-testing: ${TESTS}
>@${MESSAGE} start "db (teardown testing environment)"
>@docker compose rm --force --stop ; echo "$$?" > status_code
>@${MESSAGE} end "Down." "Error."
>@rm -f status_code
>@rm -rf .nextflow/
>@rm -f .nextflow.log
>@rm -f .nextflow.log.*
>@rm -rf work/
>@rm -rf results/
>@rm -f main.nf
>@rm -f configure.sh
>@rm -f nextflow.config
>@rm -f run.sh

${TESTS}: setup-testing
>@test_target=$@ ; \
    test_script=$${test_target/test-/} ; \
    test_name=$${test_script/module_tests\/test_/} ; \
    test_name=$${test_name/unit_tests\/test_/} ; \
    extension=$$(echo $$test_name | grep -o "\.sh\|\.py$$" ) ; \
    test_name=$${test_name/$$extension/} ; \
    test_name=$$(echo "$$test_name" | tr '_' ' ' ) ; \
    ${MESSAGE} start "  $$test_name"
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
     --network ${MODULE_NAME}_isolated_temporary_test \
     --mount type=bind,src=${PACKAGE_DIRECTORY},dst=/mount_sources \
     -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
     /bin/bash -c "$$test_cmd" ; \
    echo "$$?" > status_code
>@${MESSAGE} end "Passed." "Failed."
>@rm -f status_code

clean:
>@rm -f ${WHEEL_FILENAME}
>@rm -f initialize_schema.sql
>@rm -rf schema.sql
>@rm -f status_code
>@rm -f err_log.*.txt
>@rm -rf requirements.txt
>@rm -rf specific_requirements.txt
>@rm -rf Dockerfile
>@rm -rf .nextflow/
>@rm -f .nextflow.log
>@rm -f .nextflow.log.*
>@rm -rf work/
>@rm -rf results/
>@rm -f main.nf
>@rm -f configure.sh
>@rm -f nextflow.config
>@rm -f run.sh
