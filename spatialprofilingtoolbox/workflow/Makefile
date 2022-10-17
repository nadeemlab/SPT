.RECIPEPREFIX = >

UNIT_TEST_FILES := $(wildcard unit_tests/test_*.sh ) $(wildcard unit_tests/test_*.py )
UNIT_TESTS := $(foreach test_file,$(UNIT_TEST_FILES),test-$(test_file))

MODULE_TEST_FILES := $(wildcard module_tests/test_*.sh ) $(wildcard module_tests/test_*.py )
MODULE_TESTS := $(foreach test_file,$(MODULE_TEST_FILES),test-$(test_file))

build-dockerfile: Dockerfile

Dockerfile:
>@cat ${BUILD_SCRIPTS_LOCATION}/Dockerfile.base ./Dockerfile.append > Dockerfile

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
    source ../../venvs/workflow/bin/activate ; \
    $$executor $$test_script ; echo "$$?" > status_code ; \
    deactivate
>@${MESSAGE} end "Passed." "Failed."
>@rm -f status_code

module-tests: ${MODULE_TESTS}

${MODULE_TESTS}:
>@cd ${PACKAGE_DIRECTORY}/db; docker compose up -d && \
    bash ../../building/poll_container_readiness.sh \
     spt-db-testing && \
     cd ${PACKAGE_DIRECTORY}/workflow
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
    test_cmd="cd /mount_sources/workflow/; $$executor $$test_script" ; \
    docker run \
     --rm \
     --network host \
     --mount type=bind,src=${PACKAGE_DIRECTORY},dst=/mount_sources \
     -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
     /bin/bash -c "$$test_cmd"; \
      echo "$$?" > status_code
>@${MESSAGE} end "Passed." "Failed."
>@docker compose --project-directory ${PACKAGE_DIRECTORY}/db/ rm --force --stop
>@rm -f .nextflow.log*
>@rm -rf .nextflow/
>@rm -f configure.sh
>@rm -f run.sh
>@rm -f main.nf
>@rm -f nextflow.config
>@rm -rf work/
>@rm -rf results/
>@rm -f status_code

clean:
>@rm -f Dockerfile
>@rm -f ${WHEEL_FILENAME}
>@rm -f .nextflow.log*
>@rm -rf .nextflow/
>@rm -f configure.sh
>@rm -f run.sh
>@rm -f main.nf
>@rm -f nextflow.config
>@rm -rf work/
>@rm -rf results/
>@rm -f status_code
>@rm -rf requirements.txt
>@rm -rf specific_requirements.txt
