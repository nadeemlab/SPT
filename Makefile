.RECIPEPREFIX = >
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

PYTHON := python
BUILD_SCRIPTS_LOCATION := ${PWD}/build_scripts
BUILD_SCRIPTS_LOCATION_RELATIVE := build_scripts
BUILD_LOCATION := ${PWD}/build
BUILD_LOCATION_RELATIVE := build
TEST_LOCATION := ${PWD}/test
MESSAGE := bash ${BUILD_SCRIPTS_LOCATION}/verbose_command_wrapper.sh

help:
>@${MESSAGE} print ' The main targets are:'
>@${MESSAGE} print '  '
>@${MESSAGE} print '      make release-package'
>@${MESSAGE} print '          Build the Python package wheel and push it to PyPI.'
>@${MESSAGE} print ' '
>@${MESSAGE} print '      make build-docker-images'
>@${MESSAGE} print '          Build the Docker images.'
>@${MESSAGE} print ' '
>@${MESSAGE} print '      make build-and-push-docker-images'
>@${MESSAGE} print '          Build the Docker images and push them to DockerHub repositories.'
>@${MESSAGE} print ' '
>@${MESSAGE} print '      make test'
>@${MESSAGE} print '          Do unit and module tests.'
>@${MESSAGE} print ' '
>@${MESSAGE} print '      make [unit | module]-test-[apiserver | countsserver | db | workflow | ]'
>@${MESSAGE} print '          Do only the unit or module tests for the indicated module.'
>@${MESSAGE} print ' '
>@${MESSAGE} print '      make clean'
>@${MESSAGE} print '          Attempt to remove all build or partial-build artifacts.'
>@${MESSAGE} print ' '
>@${MESSAGE} print '      make help'
>@${MESSAGE} print '          Show this text.'
>@${MESSAGE} print ' '
>@${MESSAGE} print ' Use VERBOSE=1 to show command outputs.'
>@${MESSAGE} print ' '

LOCAL_USERID := $(shell id -u)
PACKAGE_NAME := spatialprofilingtoolbox
BUILD_RECIPES_DIRECTORY := ${BUILD_SCRIPTS_LOCATION_RELATIVE}/${PACKAGE_NAME}
VERSION := $(shell cat pyproject.toml | grep version | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
WHEEL_FILENAME := ${PACKAGE_NAME}-${VERSION}-py3-none-any.whl
DOCKER_ORG_NAME := nadeemlab
DOCKER_REPO_PREFIX := spt
DOCKERIZED_SUBMODULES := apiserver countsserver db workflow
DOCKERFILE_SOURCES := $(wildcard ${BUILD_LOCATION_RELATIVE}/*/Dockerfile.*)
DOCKERFILE_TARGETS := $(foreach submodule,$(DOCKERIZED_SUBMODULES),${BUILD_LOCATION_RELATIVE}/$(submodule)/Dockerfile)
DOCKER_BUILD_TARGETS := $(foreach submodule,$(DOCKERIZED_SUBMODULES),${BUILD_LOCATION_RELATIVE}/$(submodule)/docker.built)
DOCKER_PUSH_TARGETS := $(foreach submodule,$(DOCKERIZED_SUBMODULES),docker-push-${PACKAGE_NAME}/$(submodule))
MODULE_TEST_TARGETS := $(foreach submodule,$(DOCKERIZED_SUBMODULES),module-test-$(submodule))
UNIT_TEST_TARGETS := $(foreach submodule,$(DOCKERIZED_SUBMODULES),unit-test-$(submodule))
COMPLETIONS_SOURCE_DIRECTORY := ${PWD}/${PACKAGE_NAME}/entry_point
DB_SOURCE_DIRECTORY := ${PWD}/${PACKAGE_NAME}/db
WORKFLOW_SOURCE_DIRECTORY := ${PWD}/${PACKAGE_NAME}/workflow
PACKAGE_SOURCE_DIRECTORY := ${PWD}/${PACKAGE_NAME}
PACKAGE_SOURCE_DIRECTORY_RELATIVE := ${PACKAGE_NAME}
COMPLETIONS_BUILD_DIRECTORY := ${BUILD_LOCATION}/entry_point
DB_BUILD_DIRECTORY := ${BUILD_LOCATION}/db
WORKFLOW_BUILD_DIRECTORY := ${BUILD_LOCATION}/workflow
PACKAGE_BUILD_DIRECTORY := ${BUILD_LOCATION}
APISERVER_TEST_DIRECTORY := ${TEST_LOCATION}/apiserver
COUNTSSERVER_TEST_DIRECTORY := ${TEST_LOCATION}/countsserver
DB_TEST_DIRECTORY := ${TEST_LOCATION}/db
WORKFLOW_TEST_DIRECTORY := ${TEST_LOCATION}/workflow
export

BASIC_PACKAGE_SOURCE_FILES := $(shell find ${PACKAGE_NAME} -type f | grep -v 'schema.sql$$' | grep -v '/Dockerfile$$' | grep -v '/Dockerfile.*$$' | grep -v '/Makefile$$' | grep -v '/unit_tests/' | grep -v '/module_tests/' | grep -v '/status_code$$' | grep -v '/spt-completion.sh$$' | grep -v '${PACKAGE_NAME}/entry_point/venv/' | grep -v 'requirements.txt$$' | grep -v '/current_time.txt$$' | grep -v '/initiation_message_size.txt$$' | grep -v '/.nextflow.log$$' | grep -v '/.nextflow/' | grep -v '/main.nf$$' | grep -v '/configure.sh$$' | grep -v '/nextflow.config$$' | grep -v '/run.sh$$' | grep -v '/work/' | grep -v '/results/' | grep -v '/docker.built$$' | grep -v '/compose.yaml$$')
BASIC_PACKAGE_BUILD_FILES := $(shell find ${BUILD_LOCATION} -type f | grep -v 'schema.sql$$' | grep -v '/Dockerfile$$' | grep -v '/Dockerfile.*$$' | grep -v '/Makefile$$' | grep -v '/unit_tests/' | grep -v '/module_tests/' | grep -v '/status_code$$' | grep -v '/spt-completion.sh$$' | grep -v '${COMPLETIONS_BUILD_DIRECTORY}/venv/' | grep -v 'requirements.txt$$' | grep -v '/current_time.txt$$' | grep -v '/initiation_message_size.txt$$' | grep -v '/.nextflow.log$$' | grep -v '/.nextflow/' | grep -v '/main.nf$$' | grep -v '/configure.sh$$' | grep -v '/nextflow.config$$' | grep -v '/run.sh$$' | grep -v '/work/' | grep -v '/results/' | grep -v '/docker.built$$' | grep -v '/compose.yaml$$')
COMPLETIONS_DEPENDENCIES := ${BASIC_PACKAGE_SOURCE_FILES} ${BASIC_PACKAGE_BUILD_FILES}
PACKAGE_SOURCE_FILES_WITH_COMPLETIONS := ${BASIC_PACKAGE_SOURCE_FILES} ${BASIC_PACKAGE_BUILD_FILES} ${COMPLETIONS_BUILD_DIRECTORY}/spt-completion.sh pyproject.toml

export SHELL := ${BUILD_SCRIPTS_LOCATION}/status_messages_only_shell.sh

ifdef VERBOSE
export .SHELLFLAGS := -c -super-verbose
else
export .SHELLFLAGS := -c -not-super-verbose
endif

release-package: development-image check-for-pypi-credentials development-image
>@${MESSAGE} start "Uploading spatialprofilingtoolbox==${VERSION} to PyPI"
>@cp ~/.pypirc .
>@docker run -u ${LOCAL_USERID} --rm --mount type=bind,src=${PWD},dst=/mount_sources -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest /bin/bash -c 'cd /mount_sources; PYTHONDONTWRITEBYTECODE=1 python -m twine upload --config-file .pypirc --repository ${PACKAGE_NAME} dist/${WHEEL_FILENAME} ' ; echo "$$?" > status_code
>@${MESSAGE} end "Uploaded." "Error."
>@rm -f .pypirc

check-for-pypi-credentials:
>@${MESSAGE} start "Checking for PyPI credentials in ~/.pypirc for spatialprofilingtoolbox"
>@${PYTHON} ${BUILD_SCRIPTS_LOCATION}/check_for_credentials.py pypi ; echo "$$?" > status_code
>@${MESSAGE} end "Found." "Not found."

development-image: ${PACKAGE_SOURCE_FILES_WITH_COMPLETIONS} ${BUILD_SCRIPTS_LOCATION}/development.Dockerfile
>@${MESSAGE} start "Building development image"
>@cp ${BUILD_SCRIPTS_LOCATION}/.dockerignore . 
>@docker build \
     --rm \
     -f ${BUILD_SCRIPTS_LOCATION}/development.Dockerfile \
     -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
     --build-arg WHEEL_FILENAME=$${WHEEL_FILENAME} \
     . ; echo "$$?" > status_code ; \
    status_code=$$(cat status_code) ; \
    if [[ "$$status_code" == "0" ]]; \
    then \
        if [ ! -d dist/ ]; then mkdir dist ; fi; \
        docker run --rm -v $$(pwd)/dist:/buffer ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development /bin/sh -c "cp dist/${WHEEL_FILENAME} /buffer; chown ${LOCAL_USERID}:${LOCAL_USERID} /buffer/*; "; \
    fi 
>@status_code=$$(cat status_code); \
    if [[ "$$status_code" == "0" ]]; \
    then \
        touch development-image ; \
    fi
>@${MESSAGE} end "Built." "Build failed."
>@rm -f .dockerignore

print-source-files:
>@echo "${PACKAGE_SOURCE_FILES_WITH_COMPLETIONS}" | tr ' ' '\n'

# Go into build/entry_point and use the makefile to create the shell completion script
${COMPLETIONS_BUILD_DIRECTORY}/spt-completion.sh: ${COMPLETIONS_DEPENDENCIES}
>@${MAKE} SHELL=$(SHELL) --no-print-directory -C ${COMPLETIONS_BUILD_DIRECTORY} spt-completion.sh

build-and-push-docker-images: ${DOCKER_PUSH_TARGETS}

${DOCKER_PUSH_TARGETS}: build-docker-images check-for-docker-credentials
>@submodule_directory=$$(echo $@ | sed 's/^docker-push-//g') ; \
    submodule_version=$$(grep '^__version__ = ' $$submodule_directory/__init__.py |  grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') ;\
    submodule_name=$$(echo $$submodule_directory | sed 's/spatialprofilingtoolbox\///g') ; \
    repository_name=${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-$$submodule_name ; \
    ${MESSAGE} start "Pushing Docker container $$repository_name"
>@submodule_directory=$$(echo $@ | sed 's/^docker-push-//g') ; \
    submodule_version=$$(grep '^__version__ = ' $$submodule_directory/__init__.py |  grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') ;\
    echo "$$submodule_version"; \
    submodule_name=$$(echo $$submodule_directory | sed 's/spatialprofilingtoolbox\///g') ; \
    echo "$$submodule_name"; \
    repository_name=${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-$$submodule_name ; \
    echo "$$repository_name"; \
    docker push $$repository_name:$$submodule_version ; \
    exit_code1=$$?; \
    docker push $$repository_name:latest ; \
    exit_code2=$$?; \
    exit_code=$$(( exit_code1 + exit_code2 )); echo "$$exit_code" > status_code
>@${MESSAGE} end "Pushed." "Not pushed."

check-for-docker-credentials:
>@${MESSAGE} start "Checking for Docker credentials in ~/.docker/config.json"
>@${PYTHON} ${BUILD_SCRIPTS_LOCATION}/check_for_credentials.py docker ; status="$$?"; echo "$$status" > status_code; if [[ "$$status" == "0" ]]; then touch check-for-docker-credentials; fi;
>@${MESSAGE} end "Found." "Not found."

build-docker-images: ${DOCKER_BUILD_TARGETS}

${DOCKER_BUILD_TARGETS}: ${DOCKERFILE_TARGETS} development-image check-docker-daemon-running check-for-docker-credentials
>@submodule_directory=$$(echo $@ | sed 's/\/docker.built//g') ; \
    dockerfile=$${submodule_directory}/Dockerfile ; \
    submodule_name=$$(echo $$submodule_directory | sed 's/${BUILD_LOCATION_RELATIVE}\///g') ; \
    submodule_version=$$(grep '^__version__ = ' ${PACKAGE_SOURCE_DIRECTORY_RELATIVE}/$$submodule_name/__init__.py |  grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') ;\
    repository_name=${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-$$submodule_name ; \
    ${MESSAGE} start "Building Docker image $$repository_name"
>@submodule_directory=$$(echo $@ | sed 's/\/docker.built//g') ; \
    dockerfile=$${submodule_directory}/Dockerfile ; \
    submodule_name=$$(echo $$submodule_directory | sed 's/${BUILD_LOCATION_RELATIVE}\///g') ; \
    submodule_version=$$(grep '^__version__ = ' ${PACKAGE_SOURCE_DIRECTORY_RELATIVE}/$$submodule_name/__init__.py |  grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') ;\
    repository_name=${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-$$submodule_name ; \
    cp dist/${WHEEL_FILENAME} $$submodule_directory ; \
    cp $$submodule_directory/Dockerfile ./Dockerfile ; \
    cp ${BUILD_SCRIPTS_LOCATION}/.dockerignore . ; \
    if [ ! -f $$submodule_directory/requirements.txt ]; then bash ${BUILD_SCRIPTS_LOCATION}/create_requirements.sh > $$submodule_directory/requirements.txt ; fi; \
    if [ ! -f $$submodule_directory/specific_requirements.txt ]; then bash ${BUILD_SCRIPTS_LOCATION}/create_requirements.sh $$submodule_name > $$submodule_directory/specific_requirements.txt ; fi; \
    docker build \
     -f ./Dockerfile \
     -t $$repository_name:$$submodule_version \
     -t $$repository_name:latest \
     --build-arg version=$$submodule_version \
     --build-arg service_name=$$submodule_name \
     --build-arg WHEEL_FILENAME=$${WHEEL_FILENAME} \
     $$submodule_directory ; echo "$$?" > status_code; \
    if [[ "$$(cat status_code)" == "0" ]]; \
    then \
        touch $@ ;\
    fi
>@${MESSAGE} end "Built." "Build failed."
>@submodule_directory=$$(echo $@ | sed 's/\/docker.built//g') ; \
    rm $$submodule_directory/${WHEEL_FILENAME} ; \
    rm ./Dockerfile ; \
    rm ./.dockerignore ; \

${DOCKERFILE_TARGETS}: development-image ${BUILD_SCRIPTS_LOCATION}/Dockerfile.base ${DOCKERFILE_SOURCES}
>@submodule_directory=$$(echo $@ | sed 's/Dockerfile//g' ) ; \
    ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory Dockerfile

check-docker-daemon-running:
>@${MESSAGE} start "Checking that Docker daemon is running"
>@docker stats --no-stream ; echo "$$?" > status_code
>@${MESSAGE} end "Running." "Not running."
>@status_code=$$(cat status_code); \
    if [ $$status_code -gt 0 ] ; \
    then \
        ${MESSAGE} start "Attempting to start Docker daemon" ; \
        bash ${BUILD_SCRIPTS_LOCATION}/start_docker_daemon.sh ; echo "$$?" > status_code ; \
        status_code=$$(cat status_code); \
        if [ $$status_code -eq 1 ] ; \
        then \
            ${MESSAGE} end "--" "Timed out." ; \
        else \
            ${MESSAGE} end "Started." "Failed to start." ; \
        fi ; \
    fi ; \
    touch check-docker-daemon-running

test: unit-tests module-tests

module-tests: ${MODULE_TEST_TARGETS}

${MODULE_TEST_TARGETS}: development-image data-loaded-image-1 data-loaded-image-1and2 ${DOCKER_BUILD_TARGETS} clean-network-environment
>@submodule_directory=$$(echo $@ | sed 's/^module-test-/${BUILD_LOCATION_RELATIVE}\//g') ; \
    ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory module-tests ;

unit-tests: ${UNIT_TEST_TARGETS}

${UNIT_TEST_TARGETS}: development-image data-loaded-image-1 data-loaded-image-1and2 ${DOCKER_BUILD_TARGETS} clean-network-environment
>@submodule_directory=$$(echo $@ | sed 's/^unit-test-/${BUILD_LOCATION_RELATIVE}\//g') ; \
    ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory unit-tests ;

data-loaded-image-%: ${BUILD_LOCATION_RELATIVE}/db/docker.built development-image ${BUILD_SCRIPTS_LOCATION}/import_test_dataset%.sh
>@${MESSAGE} start "Building test-data-loaded spt-db image ($*)"
>@cp ${BUILD_SCRIPTS_LOCATION}/.dockerignore . 
>@docker container create --name temporary-spt-db-preloading --network host -e POSTGRES_PASSWORD=postgres -e PGDATA=${PWD}/.postgresql/pgdata ${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-db:latest ; \
    docker container start temporary-spt-db-preloading && \
    bash ${BUILD_SCRIPTS_LOCATION}/poll_container_readiness_direct.sh temporary-spt-db-preloading && \
    pipeline_cmd="cd /mount_sources/; bash build_scripts/import_test_dataset$*.sh ; rm -rf .nextflow; rm -f .nextflow.log ; rm -f .nextflow.log.* ; rm -rf .nextflow/ ; rm -f configure.sh ; rm -f run.sh ; rm -f main.nf ; rm -f nextflow.config ; rm -rf work/ ; rm -rf results/; "; \
    docker run \
     --rm \
     --network container:temporary-spt-db-preloading \
     --mount type=bind,src=${PWD},dst=/mount_sources \
     -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
     /bin/bash -c \
     "$$pipeline_cmd" && \
     docker commit temporary-spt-db-preloading ${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-db-preloaded-$*:latest && \
     docker container rm --force temporary-spt-db-preloading ; \
    allstatus=("$${PIPESTATUS[@]}") ; \
    if [[ "$${allstatus[0]}" == "0" ]] ; \
    then \
        status_code=0 ; \
    else \
        status_code=1 ; \
    fi ; \
    echo $$status_code > status_code
>@status_code=$$(cat status_code); \
    if [[ "$$status_code" == "0" ]]; \
    then \
        touch data-loaded-image-$* ; \
    fi
>@${MESSAGE} end "Built." "Build failed."
>@rm -f .dockerignore

clean: clean-files clean-network-environment

clean-files:
>@rm -rf ${PACKAGE_NAME}.egg-info/
>@rm -rf dist/
>@rm -f .initiation_message_size
>@rm -f .current_time.txt
>@rm -f ${BUILD_LOCATION}/*/.initiation_message_size
>@rm -f ${BUILD_LOCATION}/*/.current_time.txt
>@${MAKE} SHELL=$(SHELL) --no-print-directory -C ${BUILD_LOCATION}/entry_point/ clean
>@for submodule in ${DOCKERIZED_SUBMODULES} ; do \
        submodule_directory=${BUILD_LOCATION}/$$submodule ; \
        ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory clean ; \
        rm -rf $$submodule_directory/docker.built ; \
    done
>@rm -f Dockerfile
>@rm -f .dockerignore
>@rm -rf spatialprofilingtoolbox.egg-info/
>@rm -rf __pycache__/
>@rm -f development-image
>@rm -f data-loaded-image-1
>@rm -f data-loaded-image-2
>@rm -f data-loaded-image-1and2
>@rm -f .nextflow.log; rm -f .nextflow.log.*; rm -rf .nextflow/; rm -f configure.sh; rm -f run.sh; rm -f main.nf; rm -f nextflow.config; rm -rf work/; rm -rf results/
>@rm -f status_code
>@rm -f check-docker-daemon-running
>@rm -f check-for-docker-credentials

docker-compositions-rm: check-docker-daemon-running
>@${MESSAGE} start "Running docker compose rm (remove)"
>@docker compose --project-directory ./build/apiserver/ rm --force --stop ; status_code1="$$?" ; \
    docker compose --project-directory ./build/countsserver/ rm --force --stop ; status_code2="$$?" ; \
    docker compose --project-directory ./build/db/ rm --force --stop ; status_code3="$$?" ; \
    docker compose --project-directory ./build/workflow/ rm --force --stop ; status_code4="$$?" ; \
    status_code=$$(( status_code1 + status_code2 + status_code3 + status_code4 )) ; echo $$status_code > status_code
>@docker container rm --force temporary-spt-db-preloading
>@${MESSAGE} end "Down." "Error."

clean-network-environment: docker-compositions-rm
