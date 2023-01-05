.RECIPEPREFIX = >

MODULE_NAME := $(shell echo "verbose-shell-override" >/dev/null ; pwd | grep -o '[^/]\+$$' )

UNIT_TEST_FILES := $(wildcard ../../${TEST_LOCATION_RELATIVE}/${MODULE_NAME}/unit_tests/test_*.sh ) $(wildcard ../../${TEST_LOCATION_RELATIVE}/${MODULE_NAME}/unit_tests/test_*.py )
UNIT_TESTS := $(foreach test_file,$(UNIT_TEST_FILES),test-$(test_file))

MODULE_TEST_FILES := $(wildcard ../../${TEST_LOCATION_RELATIVE}/${MODULE_NAME}/module_tests/test_*.sh ) $(wildcard ../../${TEST_LOCATION_RELATIVE}/${MODULE_NAME}/module_tests/test_*.py )
MODULE_TESTS := $(foreach test_file,$(MODULE_TEST_FILES),test-$(test_file))

TESTS := ${UNIT_TESTS} ${MODULE_TESTS}

Dockerfile: Dockerfile.template
>@${MESSAGE} start "Building cggnn Dockerfile"
>@cp Dockerfile.template Dockerfile ; echo "$$?" > status_code
>@${MESSAGE} end "Built." "Not built."
>@rm -f status_code

.PHONY: setup-testing teardown-unit-testing teardown-module-testing teardown-testing

unit-tests: teardown-unit-testing
module-tests: teardown-module-testing
test: teardown-testing

setup-testing:
>@${MESSAGE} start "cggnn (setup testing environment)"
>@docker compose up -d && \
    bash ${BUILD_SCRIPTS_LOCATION}/poll_container_readiness.sh \
     spt-db-testing ; \
    echo "$$?" > status_code
>@${MESSAGE} end "Setup." "Not setup."
>@rm -f status_code

teardown-unit-testing: ${UNIT_TESTS}
>@${MESSAGE} start "cggnn (teardown testing environment)"
>@docker compose rm --force --stop ; echo "$$?" > status_code
>@${MESSAGE} end "Down." "Error."
>@rm -f status_code

teardown-module-testing: ${MODULE_TESTS}
>@${MESSAGE} start "cggnn (teardown testing environment)"
>@docker compose rm --force --stop ; echo "$$?" > status_code
>@${MESSAGE} end "Down." "Error."
>@rm -f status_code

teardown-testing: ${TESTS}
>@${MESSAGE} start "cggnn (teardown testing environment)"
>@docker compose rm --force --stop ; echo "$$?" > status_code
>@${MESSAGE} end "Down." "Error."
>@rm -f status_code

${TESTS}: setup-testing
>@test_target=$$(echo $@ | sed 's/..\/..\/${TEST_LOCATION_RELATIVE}\/${MODULE_NAME}\///g') ; \
    test_script=$${test_target/test-/} ; \
    test_name=$${test_script/module_tests\/test_/} ; \
    test_name=$${test_name/unit_tests\/test_/} ; \
    extension=$$(echo $$test_name | grep -o "\.sh\|\.py$$" ) ; \
    test_name=$${test_name/$$extension/} ; \
    test_name=$$(echo "$$test_name" | tr '_' ' ' ) ; \
    ${MESSAGE} start "  $$test_name"
>@test_target=$$(echo $@ | sed 's/..\/..\/${TEST_LOCATION_RELATIVE}\/${MODULE_NAME}\///g') ; \
    test_script=$${test_target/test-/} ; \
    test_name=$${test_script/module_tests\/test_/} ; \
    test_name=$${test_name/unit_tests\/test_/} ; \
    extension=$$(echo $$test_name | grep -o "\.sh\|\.py$$" ) ; \
    executor=none-cmd ; \
    if [[ "$$extension" == ".py" ]]; then executor=${PYTHON}; fi ; \
    if [[ "$$extension" == ".sh" ]]; then executor=bash; fi ; \
    test_cmd="cd /mount_sources/cggnn/; $$executor $$test_script" ; \
    docker run \
     --rm \
     --network ${MODULE_NAME}_isolated_temporary_test \
     --mount type=bind,src=${TEST_LOCATION},dst=/mount_sources \
     -t ${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-cggnn:latest \
     /bin/bash -c "$$test_cmd" ; \
    echo "$$?" > status_code
>@${MESSAGE} end "Passed." "Failed."
>@rm -f status_code

clean:
>@rm -f Dockerfile
>@rm -f ${WHEEL_FILENAME}
>@rm -f status_code
>@rm -rf requirements.txt
>@rm -rf specific_requirements.txt
