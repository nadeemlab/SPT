help:
	@echo ' The main targets are:'
	@echo '  '
	@echo '      make release-package'
	@echo '          Build the Python package wheel and push it to PyPI.'
	@echo ' '
	@echo '      make build-and-push-docker-containers'
	@echo '          Build the Docker images and push them to DockerHub repositories.'
	@echo ' '
	@echo '      make test'
	@echo '          Do unit, module, and integration tests.'
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

dist/${WHEEL_FILENAME}: $(shell find ${PACKAGE_NAME} -type f | grep -v 'schema.sql' | grep -v 'Dockerfile$$' ) ${PACKAGE_NAME}/entry_point/spt-completion.sh
	@build_package=$$(${PYTHON} -m pip freeze | grep build==) ; \
    "${MESSAGE}" start "Building wheel using $${build_package}"
	@${PYTHON} -m build 1>/dev/null 2> >(grep -v '_BetaConfiguration' >&2); \
    "${MESSAGE}" end "$$?" "Built." "Build failed."
	@if [ -d ${PACKAGE_NAME}.egg-info ]; then rm -rf ${PACKAGE_NAME}.egg-info/; fi
	@rm -rf dist/*.tar.gz

${PACKAGE_NAME}/entry_point/spt-completion.sh: $(shell find spatialprofilingtoolbox/ -type f | grep -v "entry_point/spt-completion.sh$$")
	@${MAKE} -C ${PACKAGE_NAME}/entry_point/ build-completions-script

build-and-push-docker-containers: ${DOCKER_PUSH_TARGETS}

${DOCKER_PUSH_TARGETS}: build-docker-containers check-for-docker-credentials
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

build-docker-containers: ${DOCKER_BUILD_TARGETS}

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

${DOCKERFILE_TARGETS}:
	@submodule_directory=$$(echo $@ | sed 's/^dockerfile-//g' ) ; \
    ${MAKE} -C $$submodule_directory build-dockerfile

check-docker-daemon-running:
	@"${MESSAGE}" start "Checking that Docker daemon is running"
	@docker stats --no-stream >/dev/null 2>&1; \
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

test:
	@echo "This target will be recursive, trying to do make test in all submodules."

clean:
	@rm -rf ${PACKAGE_NAME}.egg-info/
	@rm -rf dist/
	@rm -rf build/
	@rm -f .initiation_message_size
	@rm -f .current_time.txt
	@${MAKE} --no-print-directory -C ${PACKAGE_NAME}/entry_point/ clean
	@for submodule_directory_target in ${DOCKER_BUILD_TARGETS} ; do \
        submodule_directory=$$(echo $$submodule_directory_target | sed 's/^docker-build-//g') ; \
        ${MAKE} -C $$submodule_directory clean ; \
    done
	@rm -f Dockerfile
	@rm -f .dockerignore



