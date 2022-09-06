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
BUILD_SCRIPTS_LOCATION :=${PWD}/build_scripts
MESSAGE :="bash ${BUILD_SCRIPTS_LOCATION}/verbose_command_wrapper.sh"
unexport PYTHONDONTWRITEBYTECODE

PACKAGE_NAME := spatialprofilingtoolbox
VERSION := $(shell cat pyproject.toml | grep version | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
WHEEL_FILENAME := ${PACKAGE_NAME}-${VERSION}-py3-none-any.whl
DOCKER_ORG_NAME := nadeemlab
DOCKER_REPO_PREFIX := spt
DOCKER_BUILD_TARGETS := $(shell find ${PACKAGE_NAME}/*/Dockerfile.append | sed 's/Dockerfile.append//g' | sed 's/^/docker-build-/g' )
DOCKER_PUSH_TARGETS := $(shell find ${PACKAGE_NAME}/*/Dockerfile.append | sed 's/Dockerfile.append//g' | sed 's/^/docker-push-/g' )
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

dist/${WHEEL_FILENAME}: $(shell find ${PACKAGE_NAME} -type f) ${PACKAGE_NAME}/entry_point/spt-completion.sh
	@build_package=$$(${PYTHON} -m pip freeze | grep build==) ; \
    "${MESSAGE}" start "Building wheel using $${build_package}"
	@${PYTHON} -m build 1>/dev/null 2> >(grep -v '_BetaConfiguration' >&2); \
    "${MESSAGE}" end "$$?" "Built." "Build failed."
	@if [ -d ${PACKAGE_NAME}.egg-info ]; then rm -rf ${PACKAGE_NAME}.egg-info/; fi
	@rm -rf dist/*.tar.gz

${PACKAGE_NAME}/entry_point/spt-completion.sh: $(shell find spatialprofilingtoolbox/ -type f | grep -v "entry_point/spt-completion.sh$$")
	@${MAKE} -C ${PACKAGE_NAME}/entry_point/ build-completions-script

build-and-push-docker-containers: ${DOCKER_PUSH_TARGETS}

${DOCKER_PUSH_TARGETS}: build-docker-containers
	@submodule_directory=$$(echo $@ | sed 's/^docker-push-//g') ; \
    dockerfile=$${submodule_directory}/Dockerfile ; \
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

build-docker-containers: ${DOCKER_BUILD_TARGETS} check-for-docker-credentials

check-for-docker-credentials:
	@"${MESSAGE}" start "Checking for Docker credentials in ~/.docker/config.json"
	@result=$$(${PYTHON} ${BUILD_SCRIPTS_LOCATION}/check_for_credentials.py pypi); \
	if [[ "$$result" -eq "found" ]]; then exit_code=0; else exit_code=1; fi ;\
    "${MESSAGE}" end "$$exit_code" "Found." "Not found."

${DOCKER_BUILD_TARGETS}: dist/${WHEEL_FILENAME} check-docker-daemon-running
	@submodule_directory=$$(echo $@ | sed 's/^docker-build-//g') ; \
    dockerfile=$${submodule_directory}/Dockerfile ; \
    submodule_version=$$(grep '^__version__ = ' $$submodule_directory/__init__.py |  grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') ;\
    submodule_name=$$(echo $$submodule_directory | sed 's/spatialprofilingtoolbox\///g') ; \
    repository_name=${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-$$submodule_name ; \
    "${MESSAGE}" start "Building Docker container $$repository_name" ; \
    cp dist/${WHEEL_FILENAME} $$submodule_directory ; \
    cat ${BUILD_SCRIPTS_LOCATION}/Dockerfile.base $$submodule_directory/Dockerfile.append > Dockerfile ; \
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

check-docker-daemon-running:
	@"${MESSAGE}" start "Checking that Docker daemon is running"
	@docker stats --no-stream >/dev/null 2>&1; \
    "${MESSAGE}" end "$$?" "Running." "Not running."

test:
	@echo "This target will be recursive, trying to do make test in all submodules."

clean:
	@rm -rf ${PACKAGE_NAME}.egg-info/
	@rm -rf dist/
	@rm -rf build/
	@rm -f .initiation_message_size
	@rm -f .current_time.txt
	@${MAKE} -C ${PACKAGE_NAME}/entry_point/ clean
	@for submodule_directory_target in ${DOCKER_BUILD_TARGETS} ; do \
        submodule_directory=$$(echo $$submodule_directory_target | sed 's/^docker-//g') ; \
        for whl in $$submodule_directory/*.whl ; do \
            rm -f $$whl; \
        done ; \
        rm -f $$submodule_directory/${WHEEL_FILENAME}; \
    done
	@rm -f Dockerfile
	@rm -f .dockerignore



