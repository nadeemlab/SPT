.RECIPEPREFIX = >
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

PYTHON := python
BUILD_SCRIPTS_LOCATION := ${PWD}/building
BUILD_SCRIPTS_LOCATION_RELATIVE := building
MESSAGE := bash ${BUILD_SCRIPTS_LOCATION}/verbose_command_wrapper.sh

help:
>@${MESSAGE} print ' The main targets are:'
>@${MESSAGE} print '  '
>@${MESSAGE} print '      make release-package'
>@${MESSAGE} print '          Build the Python package wheel and push it to PyPI.'
>@${MESSAGE} print ' '
>@${MESSAGE} print '      make build-and-push-docker-images'
>@${MESSAGE} print '          Build the Docker images and push them to DockerHub repositories.'
>@${MESSAGE} print ' '
>@${MESSAGE} print '      make test'
>@${MESSAGE} print '          Do unit and module tests.'
>@${MESSAGE} print ' '
>@${MESSAGE} print '      make clean'
>@${MESSAGE} print '          Attempt to remove all build or partial-build artifacts.'
>@${MESSAGE} print ' '
>@${MESSAGE} print '      make help'
>@${MESSAGE} print '          Show this text.'

PACKAGE_NAME := spatialprofilingtoolbox
VERSION := $(shell cat pyproject.toml | grep version | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
WHEEL_FILENAME := ${PACKAGE_NAME}-${VERSION}-py3-none-any.whl
DOCKER_ORG_NAME := nadeemlab
DOCKER_REPO_PREFIX := spt
DOCKERIZED_SUBMODULES := apiserver countsserver db workflow
DOCKERFILE_TARGETS := $(foreach submodule,$(DOCKERIZED_SUBMODULES),dockerfile-${PACKAGE_NAME}/$(submodule))
DOCKER_BUILD_TARGETS := $(foreach submodule,$(DOCKERIZED_SUBMODULES),docker-build-${PACKAGE_NAME}/$(submodule))
DOCKER_PUSH_TARGETS := $(foreach submodule,$(DOCKERIZED_SUBMODULES),docker-push-${PACKAGE_NAME}/$(submodule))
MODULE_TEST_TARGETS := $(foreach submodule,$(DOCKERIZED_SUBMODULES),test-module-${PACKAGE_NAME}/$(submodule))
COMPLETIONS_DIRECTORY := ${PWD}/${PACKAGE_NAME}/entry_point
DB_DIRECTORY := ${PWD}/${PACKAGE_NAME}/db
WORKFLOW_DIRECTORY := ${PWD}/${PACKAGE_NAME}/workflow
PACKAGE_DIRECTORY := ${PWD}/${PACKAGE_NAME}
export

BASIC_PACKAGE_SOURCE_FILES := $(shell find ${PACKAGE_NAME} -type f | grep -v 'schema.sql$$' | grep -v 'Dockerfile$$' | grep -v 'Dockerfile.append$$' | grep -v 'Makefile$$' | grep -v 'unit_tests/' | grep -v 'module_tests/' | grep -v 'status_code$$' | grep -v 'spt-completion.sh$$' | grep -v '${PACKAGE_NAME}/entry_point/venv/' | grep -v 'requirements.txt$$')
COMPLETIONS_DEPENDENCIES := ${BASIC_PACKAGE_SOURCE_FILES}
PACKAGE_SOURCE_FILES_WITH_COMPLETIONS := ${BASIC_PACKAGE_SOURCE_FILES} ${PACKAGE_NAME}/entry_point/spt-completion.sh pyproject.toml

export SHELL := ${BUILD_SCRIPTS_LOCATION}/status_messages_only_shell.sh

ifdef VERBOSE
export .SHELLFLAGS := -c -super-verbose
else
export .SHELLFLAGS := -c -not-super-verbose
endif

release-package: build-wheel-for-distribution check-for-pypi-credentials development-image
>@${MESSAGE} start "Uploading spatialprofilingtoolbox==${VERSION} to PyPI"
>@docker run --rm --mount type=bind,src=${PWD},dst=/mount_sources -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest /bin/bash -c 'cd /mount_sources; PYTHONDONTWRITEBYTECODE=1 python -m twine upload --repository ${PACKAGE_NAME} dist/${WHEEL_FILENAME} ' ; echo "$$?" > status_code
>@${MESSAGE} end "Uploaded." "Error."

check-for-pypi-credentials:
>@${MESSAGE} start "Checking for PyPI credentials in ~/.pypirc for spatialprofilingtoolbox"
>@${PYTHON} ${BUILD_SCRIPTS_LOCATION}/check_for_credentials.py pypi ; echo "$$?" > status_code
>@${MESSAGE} end "Found." "Not found."

build-wheel-for-distribution: dist/${WHEEL_FILENAME}

dist/${WHEEL_FILENAME}: development-image
>@${MESSAGE} start "${PACKAGE_NAME} wheel is retrieved"
>@test -f dist/${WHEEL_FILENAME} ; echo "$$?" > status_code
>@${MESSAGE} end "to dist/" "Retrieval failed."

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
        docker run --rm -v $$(pwd)/dist:/buffer ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development /bin/sh -c "cp dist/${WHEEL_FILENAME} /buffer"; \
    fi 
>@${MESSAGE} end "Built." "Build failed."
>@rm -f .dockerignore
>@rm -rf build/
>@touch development-image

print-source-files:
>@echo "${PACKAGE_SOURCE_FILES_WITH_COMPLETIONS}" | tr ' ' '\n'

${PACKAGE_NAME}/entry_point/spt-completion.sh: ${COMPLETIONS_DEPENDENCIES}
>@${MAKE} SHELL=$(SHELL) --no-print-directory -C ${PACKAGE_NAME}/entry_point/ spt-completion.sh

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
>@${PYTHON} ${BUILD_SCRIPTS_LOCATION}/check_for_credentials.py docker ; echo "$$?" > status_code
>@${MESSAGE} end "Found." "Not found."

build-docker-images: ${DOCKER_BUILD_TARGETS}

${DOCKER_BUILD_TARGETS}: ${DOCKERFILE_TARGETS} dist/${WHEEL_FILENAME} check-docker-daemon-running
>@submodule_directory=$$(echo $@ | sed 's/^docker-build-//g') ; \
    dockerfile=$${submodule_directory}/Dockerfile ; \
    submodule_version=$$(grep '^__version__ = ' $$submodule_directory/__init__.py |  grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') ;\
    submodule_name=$$(echo $$submodule_directory | sed 's/spatialprofilingtoolbox\///g') ; \
    repository_name=${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-$$submodule_name ; \
    ${MESSAGE} start "Building Docker image $$repository_name"
>@submodule_directory=$$(echo $@ | sed 's/^docker-build-//g') ; \
    dockerfile=$${submodule_directory}/Dockerfile ; \
    submodule_version=$$(grep '^__version__ = ' $$submodule_directory/__init__.py |  grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') ;\
    submodule_name=$$(echo $$submodule_directory | sed 's/spatialprofilingtoolbox\///g') ; \
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
     $$submodule_directory ; echo "$$?" > status_code
>@${MESSAGE} end "Built." "Build failed."
>@submodule_directory=$$(echo $@ | sed 's/^docker-build-//g') ; \
    rm $$submodule_directory/${WHEEL_FILENAME} ; \
    rm ./Dockerfile ; \
    rm ./.dockerignore ; \

${DOCKERFILE_TARGETS}: development-image ${BUILD_SCRIPTS_LOCATION}/Dockerfile.base
>@submodule_directory=$$(echo $@ | sed 's/^dockerfile-//g' ) ; \
    ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory build-dockerfile

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
    fi

test: unit-tests module-tests

unit-tests: development-image
>@for submodule_directory_target in ${MODULE_TEST_TARGETS} ; do \
        submodule_directory=$$(echo $$submodule_directory_target | sed 's/^test-module-//g') ; \
        ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory unit-tests ; \
    done

module-tests: development-image
>@for submodule_directory_target in ${MODULE_TEST_TARGETS} ; do \
        submodule_directory=$$(echo $$submodule_directory_target | sed 's/^test-module-//g') ; \
        ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory module-tests ; \
    done

clean: clean-files docker-compositions-rm

clean-files:
>@rm -rf ${PACKAGE_NAME}.egg-info/
>@rm -rf dist/
>@rm -rf build/
>@rm -f .initiation_message_size
>@rm -f .current_time.txt
>@rm -f ${PACKAGE_NAME}/*/.initiation_message_size
>@rm -f ${PACKAGE_NAME}/*/.current_time.txt
>@${MAKE} SHELL=$(SHELL) --no-print-directory -C ${PACKAGE_NAME}/entry_point/ clean
>@for submodule_directory_target in ${DOCKER_BUILD_TARGETS} ; do \
        submodule_directory=$$(echo $$submodule_directory_target | sed 's/^docker-build-//g') ; \
        ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory clean ; \
    done
>@rm -f Dockerfile
>@rm -f .dockerignore
>@rm -rf spatialprofilingtoolbox.egg-info/
>@rm -rf __pycache__/
>@rm -rf build/
>@rm -rf status_code
>@rm -rf development-image

docker-compositions-rm: check-docker-daemon-running
>@${MESSAGE} start "Running docker compose rm (remove)"
>@docker compose --project-directory ./spatialprofilingtoolbox/apiserver/ rm --force --stop ; status_code1="$$?" ; \
    docker compose --project-directory ./spatialprofilingtoolbox/countsserver/ rm --force --stop ; status_code2="$$?" ; \
    docker compose --project-directory ./spatialprofilingtoolbox/db/ rm --force --stop ; status_code3="$$?" ; \
    status_code=$$(( status_code1 + status_code2 + status_code3 )) ; echo $$status_code > status_code
>@${MESSAGE} end "Down." "Error."
>@rm -rf status_code
