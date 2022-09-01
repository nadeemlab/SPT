
export SHELL := /bin/bash
PYTHON := python
BUILD_SCRIPTS_LOCATION :=${PWD}/build_scripts
MESSAGE :="bash ${BUILD_SCRIPTS_LOCATION}/verbose_command_wrapper.sh"
unexport PYTHONDONTWRITEBYTECODE

PACKAGE_NAME := spatialprofilingtoolbox
VERSION := $(shell cat pyproject.toml | grep version | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
WHEEL_FILENAME := ${PACKAGE_NAME}-${VERSION}-py3-none-any.whl
export

release-package: build-wheel-for-distribution check-for-pypi-credentials
	@"${MESSAGE}" start "Uploading spatialprofilingtoolbox==${VERSION} to PyPI"
	@${PYTHON} -m twine upload --repository ${PACKAGE_NAME} dist/${WHEEL_FILENAME} ; \
    "${MESSAGE}" end "$$?" "Uploaded." "Error."

check-for-pypi-credentials:
	@"${MESSAGE}" start "Checking for PyPI credentials in ~/.pypirc for spatialprofilingtoolbox"
	@result=$$(${PYTHON} ${BUILD_SCRIPTS_LOCATION}/check_for_credentials.py pypi); \
	if [[ "$$result" -eq "found" ]]; then result_code=0; else result_code=1; fi ;\
    "${MESSAGE}" end "$$result_code" "Found." "Not found."

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

build-and-push-docker-containers: check-for-docker-credentials
	@echo "This target will be recursive, trying to do make build-and-push-docker-container in all submodules. Use docker build --build-arg submodule_version=y.y.y in place of the current template system."

check-for-docker-credentials:
	@"${MESSAGE}" start "Checking for Docker credentials in ~/.docker/config.json"
	@result=$$(${PYTHON} ${BUILD_SCRIPTS_LOCATION}/check_for_credentials.py pypi); \
	if [[ "$$result" -eq "found" ]]; then result_code=0; else result_code=1; fi ;\
    "${MESSAGE}" end "$$result_code" "Found." "Not found."

test:
	@echo "This target will be recursive, trying to do make test in all submodules."

clean:
	@rm -rf ${PACKAGE_NAME}.egg-info/
	@rm -rf dist/
	@rm -rf build/
	@rm -f .initiation_message_size
	@rm -f .current_time.txt
	@${MAKE} -C ${PACKAGE_NAME}/entry_point/ clean
