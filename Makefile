.RECIPEPREFIX = >
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

help:
>@echo ' The main targets are:'
>@echo '  '
>@echo '      make release-package'
>@echo '          Build the Python package wheel and push it to PyPI.'
>@echo ' '
>@echo '      make build-and-push-docker-images'
>@echo '          Build the Docker images and push them to DockerHub repositories.'
>@echo ' '
>@echo '      make test'
>@echo '          Do unit and module tests.'
>@echo ' '
>@echo '      make clean'
>@echo '          Attempt to remove all build or partial-build artifacts.'
>@echo ' '
>@echo '      make help'
>@echo '          Show this text.'

PYTHON := python
BUILD_SCRIPTS_LOCATION :=${PWD}/building
MESSAGE := bash ${BUILD_SCRIPTS_LOCATION}/verbose_command_wrapper.sh
unexport PYTHONDONTWRITEBYTECODE

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
DEVELOPMENT_EXTRAS_NAMES := apiserver db workflow all
DEVELOPMENT_VENV_TARGETS := $(foreach extra,$(DEVELOPMENT_EXTRAS_NAMES),venvs/$(extra)/touch.txt)
export

BASIC_PACKAGE_SOURCE_FILES := $(shell find ${PACKAGE_NAME} -type f | grep -v 'schema.sql' | grep -v 'Dockerfile$$' | grep -v 'Dockerfile.append$$' | grep -v 'Makefile$$' | grep -v 'unit_tests/' | grep -v 'module_tests/' | grep -v 'status_code' | grep -v 'spt-completion.sh$$' )
PACKAGE_SOURCE_FILES := ${BASIC_PACKAGE_SOURCE_FILES} ${PACKAGE_NAME}/entry_point/spt-completion.sh  pyproject.toml
COMPLETIONS_DEPENDENCIES := ${BASIC_PACKAGE_SOURCE_FILES}

export SHELL := ${BUILD_SCRIPTS_LOCATION}/status_messages_only_shell.sh

ifdef VERBOSE
export .SHELLFLAGS := -c -super-verbose
else
export .SHELLFLAGS := -c -not-super-verbose
endif

print-detected-version:
>echo ${VERSION}

release-package: build-wheel-for-distribution check-for-pypi-credentials
>@${MESSAGE} start "Uploading spatialprofilingtoolbox==${VERSION} to PyPI"
>@${PYTHON} -m twine upload --repository ${PACKAGE_NAME} dist/${WHEEL_FILENAME} ; echo "$$?" > status_code
>@${MESSAGE} end "Uploaded." "Error."

check-for-pypi-credentials:
>@${MESSAGE} start "Checking for PyPI credentials in ~/.pypirc for spatialprofilingtoolbox"
>@${PYTHON} ${BUILD_SCRIPTS_LOCATION}/check_for_credentials.py pypi; echo "$$?" > status_code
>@${MESSAGE} end "Found." "Not found."

build-wheel-for-distribution: dist/${WHEEL_FILENAME}

dist/${WHEEL_FILENAME}: ${PACKAGE_SOURCE_FILES}
>@build_package=$$(${PYTHON} -m pip freeze | grep build==) ; \
    ${MESSAGE} start "Building ${PACKAGE_NAME} wheel using $${build_package}"
>@${PYTHON} -m build 2> >(grep -v '_BetaConfiguration' >&2); echo "$$?" > status_code
>@${MESSAGE} end "Built." "Build failed."
>@if [ -d ${PACKAGE_NAME}.egg-info ]; then rm -rf ${PACKAGE_NAME}.egg-info/; fi
>@rm -rf dist/*.tar.gz

print-source-files:
>@echo "${PACKAGE_SOURCE_FILES}" | tr ' ' '\n'

${PACKAGE_NAME}/entry_point/spt-completion.sh: virtual-environments-from-source-not-wheel ${COMPLETIONS_DEPENDENCIES}
>@${MAKE} SHELL=$(SHELL) --no-print-directory -C ${PACKAGE_NAME}/entry_point/ build-completions-script

build-and-push-docker-images: ${DOCKER_PUSH_TARGETS}

${DOCKER_PUSH_TARGETS}: build-docker-images check-for-docker-credentials
>@submodule_directory=$$(echo $@ | sed 's/^docker-push-//g') ; \
    submodule_version=$$(grep '^__version__ = ' $$submodule_directory/__init__.py |  grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') ;\
    submodule_name=$$(echo $$submodule_directory | sed 's/spatialprofilingtoolbox\///g') ; \
    repository_name=${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-$$submodule_name ; \
    ${MESSAGE} start "Pushing Docker container $$repository_name"
>@submodule_directory=$$(echo $@ | sed 's/^docker-push-//g') ; \
    submodule_version=$$(grep '^__version__ = ' $$submodule_directory/__init__.py |  grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') ;\
    submodule_name=$$(echo $$submodule_directory | sed 's/spatialprofilingtoolbox\///g') ; \
    repository_name=${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-$$submodule_name ; \
    docker push $$repository_name:$$submodule_version ; \
    exit_code1=$$?; \
    docker push $$repository_name:latest ; \
    exit_code2=$$?; \
    exit_code=$$(( exit_code1 + exit_code2 )); cat "$$exit_code" > status_code
>@${MESSAGE} end "Pushed." "Not pushed."

check-for-docker-credentials:
>@${MESSAGE} start "Checking for Docker credentials in ~/.docker/config.json"
>@${PYTHON} ${BUILD_SCRIPTS_LOCATION}/check_for_credentials.py pypi; echo "$$?" > status_code
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
    rm ./.dockerignore

${DOCKERFILE_TARGETS}: virtual-environments-from-source-not-wheel
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

unit-tests: development-virtual-environments
>@for submodule_directory_target in ${MODULE_TEST_TARGETS} ; do \
        submodule_directory=$$(echo $$submodule_directory_target | sed 's/^test-module-//g') ; \
        ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory unit-tests ; \
    done

module-tests: development-virtual-environments
>@for submodule_directory_target in ${MODULE_TEST_TARGETS} ; do \
        submodule_directory=$$(echo $$submodule_directory_target | sed 's/^test-module-//g') ; \
        ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory module-tests ; \
    done

development-virtual-environments: ${DEVELOPMENT_VENV_TARGETS}

virtual-environments-from-source-not-wheel: venvs/building/touch.txt

${DEVELOPMENT_VENV_TARGETS}: dist/${WHEEL_FILENAME} venvs/touch.txt
>@extra=$$(echo $@ | sed 's/venvs\///g' | sed 's/\/touch.txt//g' ) ; \
    ${MESSAGE} start "Creating virtual environment [$$extra]"
>@extra=$$(echo $@ | sed 's/venvs\///g' | sed 's/\/touch.txt//g' ) ; \
    rm -rf venvs/$$extra ; \
    ${PYTHON} -m venv venvs/$$extra && \
    source venvs/$$extra/bin/activate && \
    ${PYTHON} -m pip install "dist/${WHEEL_FILENAME}[$$extra]" && \
    deactivate ; echo "$$?" > status_code
>@${MESSAGE} end "Created." "Not created."
>@status_code=$$(cat status_code) ; \
    if [ $$status_code -eq 0 ] ; then \
        extra=$$(echo $@ | sed 's/venvs\///g' | sed 's/\/touch.txt//g' ) ; \
        touch venvs/$$extra/touch.txt ; \
    fi

venvs/building/touch.txt: venvs/touch.txt
>@${MESSAGE} start "Creating virtual environment [building]"
>@${PYTHON} -m venv venvs/building && \
    source venvs/building/bin/activate && \
    ${PYTHON} -m pip install ".[building]" && \
    deactivate ; echo "$$?" > status_code 
>@${MESSAGE} end "Created." "Not created."
>@status_code=$$(cat status_code) ; \
    if [ $$status_code -eq 0 ] ; then \
        touch venvs/building/touch.txt ; \
    fi
>@rm -rf spatialprofilingtoolbox.egg-info/
>@rm -rf __pycache__/
>@rm -rf build/

venvs/touch.txt:
>@if ! [[ -d "venvs" ]]; \
    then mkdir venvs/ ; touch venvs/touch.txt; \
    fi

clean: clean-files docker-compositions-rm

clean-files:
>@rm -rf ${PACKAGE_NAME}.egg-info/
>@rm -rf dist/
>@rm -rf build/
>@rm -f .initiation_message_size
>@rm -f .current_time.txt
>@${MAKE} SHELL=$(SHELL) --no-print-directory -C ${PACKAGE_NAME}/entry_point/ clean
>@for submodule_directory_target in ${DOCKER_BUILD_TARGETS} ; do \
        submodule_directory=$$(echo $$submodule_directory_target | sed 's/^docker-build-//g') ; \
        ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory clean ; \
    done
>@rm -f Dockerfile
>@rm -f .dockerignore
>@rm -rf venvs/
>@rm -rf spatialprofilingtoolbox.egg-info/
>@rm -rf __pycache__/
>@rm -rf build/
>@rm -rf status_code

docker-compositions-rm: check-docker-daemon-running
>@${MESSAGE} start "Running docker compose rm (remove)"
>@docker compose --project-directory ./spatialprofilingtoolbox/apiserver/ rm --force --stop ; status_code1="$$?" ; \
    docker compose --project-directory ./spatialprofilingtoolbox/countsserver/ rm --force --stop ; status_code2="$$?" ; \
    docker compose --project-directory ./spatialprofilingtoolbox/db/ rm --force --stop ; status_code3="$$?" ; \
    status_code=$$(( status_code1 + status_code2 + status_code3 )) ; echo $$status_code > status_code
>@${MESSAGE} end "Down." "Error."
>@rm -rf status_code
