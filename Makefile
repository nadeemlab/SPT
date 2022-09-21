help:
	@echo ' The main targets are:'
	@echo '  '
	@echo '      make release-package'
	@echo '          Build the Python package wheel and push it to PyPI.'
	@echo ' '
	@echo '      make build-and-push-docker-images'
	@echo '          Build the Docker images and push them to DockerHub repositories.'
	@echo ' '
	@echo '      make test'
	@echo '          Do unit and module tests.'
	@echo ' '
	@echo '      make clean'
	@echo '          Attempt to remove all build or partial-build artifacts.'
	@echo ' '
	@echo '      make help'
	@echo '          Show this text.'

export SHELL := /bin/bash
PYTHON := python
BUILD_SCRIPTS_LOCATION :=${PWD}/building
MESSAGE :="bash ${BUILD_SCRIPTS_LOCATION}/verbose_command_wrapper.sh"
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
DEVELOPMENT_EXTRAS_NAMES :=  apiserver db workflow all
DEVELOPMENT_VENV_TARGETS := $(foreach extra,$(DEVELOPMENT_EXTRAS_NAMES),venvs/$(extra)/touch.txt)
export

release-package: build-wheel-for-distribution check-for-pypi-credentials
	@"${MESSAGE}" start "Uploading spatialprofilingtoolbox==${VERSION} to PyPI"
	@${PYTHON} -m twine upload --repository ${PACKAGE_NAME} dist/${WHEEL_FILENAME} ; \
    "${MESSAGE}" end "$$?" "Uploaded." "Error."

check-for-pypi-credentials:
	@"${MESSAGE}" start "Checking for PyPI credentials in ~/.pypirc for spatialprofilingtoolbox"
	@result=$$(${PYTHON} ${BUILD_SCRIPTS_LOCATION}/check_for_credentials.py pypi); \
	if [[ "$$result" -eq "found" ]]; then exit_code=0; else exit_code=1; fi ;\
    "${MESSAGE}" end "$$exit_code" "Found." "Not found."

build-wheel-for-distribution: dist/${WHEEL_FILENAME}

dist/${WHEEL_FILENAME}: $(shell find ${PACKAGE_NAME} -type f | grep -v 'schema.sql' | grep -v 'Dockerfile$$' | grep -v 'Dockerfile.append$$' | grep -v 'Makefile$$' | grep -v 'unit_tests/' | grep -v 'module_tests/' ) ${PACKAGE_NAME}/entry_point/spt-completion.sh pyproject.toml
	@build_package=$$(${PYTHON} -m pip freeze | grep build==) ; \
    "${MESSAGE}" start "Building ${PACKAGE_NAME} wheel using $${build_package}"
	@${PYTHON} -m build 1>/dev/null 2> >(grep -v '_BetaConfiguration' >&2); \
    "${MESSAGE}" end "$$?" "Built." "Build failed."
	@if [ -d ${PACKAGE_NAME}.egg-info ]; then rm -rf ${PACKAGE_NAME}.egg-info/; fi
	@rm -rf dist/*.tar.gz

${PACKAGE_NAME}/entry_point/spt-completion.sh: virtual-environments-from-source-not-wheel $(shell find spatialprofilingtoolbox/ -type f | grep -v "entry_point/spt-completion.sh$$")
	@${MAKE} SHELL=$(SHELL) --no-print-directory -C ${PACKAGE_NAME}/entry_point/ build-completions-script

build-and-push-docker-images: ${DOCKER_PUSH_TARGETS}

${DOCKER_PUSH_TARGETS}: build-docker-images check-for-docker-credentials
	@submodule_directory=$$(echo $@ | sed 's/^docker-push-//g') ; \
    submodule_version=$$(grep '^__version__ = ' $$submodule_directory/__init__.py |  grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') ;\
    submodule_name=$$(echo $$submodule_directory | sed 's/spatialprofilingtoolbox\///g') ; \
    repository_name=${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-$$submodule_name ; \
    "${MESSAGE}" start "Pushing Docker container $$repository_name" ; \
    docker push $$repository_name:$$submodule_version >/dev/null 2>&1 ; \
    exit_code1=$$?; \
    docker push $$repository_name:latest >/dev/null 2>&1 ; \
    exit_code2=$$?; \
    exit_code=$$(( exit_code1 + exit_code2 )); \
    "${MESSAGE}" end "$$exit_code" "Pushed." "Not pushed."

check-for-docker-credentials:
	@"${MESSAGE}" start "Checking for Docker credentials in ~/.docker/config.json"
	@result=$$(${PYTHON} ${BUILD_SCRIPTS_LOCATION}/check_for_credentials.py pypi); \
    if [[ "$$result" -eq "found" ]]; then exit_code=0; else exit_code=1; fi ;\
    "${MESSAGE}" end "$$exit_code" "Found." "Not found."

build-docker-images: ${DOCKER_BUILD_TARGETS}

${DOCKER_BUILD_TARGETS}: ${DOCKERFILE_TARGETS} dist/${WHEEL_FILENAME} check-docker-daemon-running
	@submodule_directory=$$(echo $@ | sed 's/^docker-build-//g') ; \
    dockerfile=$${submodule_directory}/Dockerfile ; \
    submodule_version=$$(grep '^__version__ = ' $$submodule_directory/__init__.py |  grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') ;\
    submodule_name=$$(echo $$submodule_directory | sed 's/spatialprofilingtoolbox\///g') ; \
    repository_name=${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-$$submodule_name ; \
    "${MESSAGE}" start "Building Docker image $$repository_name" ; \
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
     $$submodule_directory \
     >/dev/null 2>&1 ; \
    "${MESSAGE}" end "$$?" "Built." "Build failed." ; \
    rm $$submodule_directory/${WHEEL_FILENAME} ; \
    rm ./Dockerfile ; \
    rm ./.dockerignore

${DOCKERFILE_TARGETS}: virtual-environments-from-source-not-wheel
	@submodule_directory=$$(echo $@ | sed 's/^dockerfile-//g' ) ; \
    ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory build-dockerfile

check-docker-daemon-running:
	@"${MESSAGE}" start "Checking that Docker daemon is running"
	@docker stats --no-stream >/dev/null 2>&1 ; \
    result_code="$$?" ; \
    "${MESSAGE}" end "$$result_code" "Running." "Not running." ; \
    if [ $$result_code -gt 0 ] ; \
    then \
        "${MESSAGE}" start "Attempting to start Docker daemon" ; \
        bash ${BUILD_SCRIPTS_LOCATION}/start_docker_daemon.sh ; \
        result_code="$$?" ; \
        if [ $$result_code -eq 1 ] ; \
        then \
            "${MESSAGE}" end "$$result_code" "Started." "Timed out." ; \
        else \
            "${MESSAGE}" end "$$result_code" "Started." "Failed to start." ; \
        fi ; \
    fi

test: unit-tests module-tests

unit-tests: development-virtual-environments
	@for submodule_directory_target in ${MODULE_TEST_TARGETS} ; do \
        submodule_directory=$$(echo $$submodule_directory_target | sed 's/^test-module-//g') ; \
        ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory unit-tests ; \
    done

module-tests: development-virtual-environments
	@for submodule_directory_target in ${MODULE_TEST_TARGETS} ; do \
        submodule_directory=$$(echo $$submodule_directory_target | sed 's/^test-module-//g') ; \
        ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory module-tests ; \
    done

development-virtual-environments: ${DEVELOPMENT_VENV_TARGETS}

virtual-environments-from-source-not-wheel: venvs/building/touch.txt

${DEVELOPMENT_VENV_TARGETS}: dist/${WHEEL_FILENAME} venvs/touch.txt
	@extra=$$(echo $@ | sed 's/venvs\///g' | sed 's/\/touch.txt//g' ) ; \
    "${MESSAGE}" start "Creating virtual environment [$$extra]" ; \
    rm -rf venvs/$$extra ; \
	${PYTHON} -m venv venvs/$$extra && \
    source venvs/$$extra/bin/activate && \
    ${PYTHON} -m pip install "dist/${WHEEL_FILENAME}[$$extra]" >/dev/null 2>&1 && \
    deactivate ; \
    result_code="$$?" ; \
    "${MESSAGE}" end "$$result_code" "Created." "Not created." ; \
    if [ $$result_code -eq 0 ] ; then \
        touch venvs/$$extra/touch.txt ; \
    fi

venvs/building/touch.txt: venvs/touch.txt
	@extra=building ; \
    "${MESSAGE}" start "Creating virtual environment [$$extra]" ; \
    ${PYTHON} -m venv venvs/$$extra && \
    source venvs/$$extra/bin/activate && \
    ${PYTHON} -m pip install ".[$$extra]" >/dev/null 2>&1 && \
    deactivate ; \
    result_code="$$?" ; \
    "${MESSAGE}" end "$$result_code" "Created." "Not created." ; \
    if [ $$result_code -eq 0 ] ; then \
        touch venvs/$$extra/touch.txt ; \
    fi
	@rm -rf spatialprofilingtoolbox.egg-info/
	@rm -rf __pycache__/
	@rm -rf build/

venvs/touch.txt:
	@mkdir venvs/
	@touch venvs/touch.txt

clean: clean-files docker-compositions-down

clean-files:
	@rm -rf ${PACKAGE_NAME}.egg-info/
	@rm -rf dist/
	@rm -rf build/
	@rm -f .initiation_message_size
	@rm -f .current_time.txt
	@${MAKE} SHELL=$(SHELL) --no-print-directory -C ${PACKAGE_NAME}/entry_point/ clean
	@for submodule_directory_target in ${DOCKER_BUILD_TARGETS} ; do \
        submodule_directory=$$(echo $$submodule_directory_target | sed 's/^docker-build-//g') ; \
        ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory clean ; \
    done
	@rm -f Dockerfile
	@rm -f .dockerignore
	@rm -rf venvs/
	@rm -rf spatialprofilingtoolbox.egg-info/
	@rm -rf __pycache__/
	@rm -rf build/

docker-compositions-down: check-docker-daemon-running
	@"${MESSAGE}" start "Running docker compose down"
	@docker compose --project-directory ./spatialprofilingtoolbox/apiserver/ down >/dev/null 2>&1
	@docker compose --project-directory ./spatialprofilingtoolbox/countsserver/ down >/dev/null 2>&1
	@docker compose --project-directory ./spatialprofilingtoolbox/db/ down >/dev/null 2>&1
	@"${MESSAGE}" end "0" "Down." "Error."
