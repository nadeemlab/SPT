help:
	#
	# This is mainly a lightweight release-management script for coordinated
	# PyPI, DockerHub, and GitHub releases of SPT (spatialprofilingtoolbox).
	#
	# The primary target is:
	#
	#     make release
	#
	# The above includes code testing.
	#
	# You can also release just the Docker image, to a test DockerHub repository,
	# with no code testing:
	#
	#     make test-release
	#
	# You can also do just code testing:
	#
	#     make test
	#
	# or
	#
	#     make .unit-tests
	#     make .integration-tests
	#
	# The following conventions are used:
	#
	# - Targets starting with '.' like '.all-credentials-available' create empty
	#   files that are placeholders indicating an environment or build state. They
	#   are all deleted on `make clean`. This usage is called "empty target files
	#   to record events" in the GNU Make documentation.
	# - Most other targets are "PHONY", meaning that their recipes are always run
	#   again whenever these targets are checked for completion. This is because
	#   this Makefile is used for coordinating release actions rather than builds
	#   per se.
	#
	# To show this text:
	#
	#     make help
	#

# Environment setup
SHELL := /bin/bash
.DELETE_ON_ERROR:
BIN :=${PWD}/building
$(shell chmod +x ${BIN}/check_for_credentials.py)
$(shell chmod +x ${BIN}/check_commit_state.sh)
.PHONY: (\
	release \
	test-release \
	all-external-pushes \
	twine-upload \
	docker-push \
	docker-test-push \
	source-code-release-push \
	source-code-main-push \
	clean \
)
RESET:="\033[0m"
NOTE_COLOR:="\033[0m"
NOTE_COLOR_FINAL:="\033[32;1m"
ERROR_COLOR:="\033[31;1m"
DOTS_COLOR:="\033[33m"
PADDING:=...............................................................
SPACE:=" "
COMMMA:=,
LEFT_PAREN:=(
RIGHT_PAREN:=)

# Run-time and configuration variables
PYPI_CREDENTIALS := $(call credentials_available,pypi)
DOCKER_CREDENTIALS := $(call credentials_available,docker)
ifneq ("$(wildcard nextflow)","")
    NEXTFLOW := ./nextflow
else
	NEXTFLOW := $(if $(shell which nextflow),$(shell which nextflow),)
endif
PLACEHOLDERS := \
	.all-credentials-available \
	.docker-credentials-available \
	.pypi-credentials-available \
	.test \
	.unit-tests \
	.update-version \
	.commit-new-version \
	.installed-in-venv \
	.package-build \
	.on-main-branch \
	.nextflow-available \
	.controlled-source-files-unchanged
VERSION_FILE := spatialprofilingtoolbox/version.txt
DOCKER_ORG_NAME := nadeemlab
DOCKER_REPO := spt
DOCKER_TEST_REPO := spt-test
PYTHON := python3
RELEASE_TO_BRANCH := prerelease
INTEGRATION_TESTS := $(shell cd tests/integration_tests/; find . -maxdepth 1 -regex '.*\.sh$$' | sed 's:^\./:\.:g')
LIBRARY_SOURCES := $(shell find spatialprofilingtoolbox/)
LIBRARY_METADATA := setup.py requirements.txt
UNIT_TEST_SOURCES := $(shell find tests/unit_tests/*.py)
INTEGRATION_TEST_SOURCES := $(shell find tests/integration_tests/*.sh)

# Functions
credentials_available = $(shell ${BIN}/check_for_credentials.py $1)
color_in_progress = ${NOTE_COLOR}$1${SPACE}${DOTS_COLOR}$(shell padding="${PADDING}"; insertion="$1"; echo \"$${padding:$${\#insertion}}\"; )${RESET}" "
color_final = ${NOTE_COLOR_FINAL}$1${RESET}" "$(shell padding=..............................; insertion='$1'; echo \"$${padding:$${\#insertion}}\"; )" $2\n"
color_error = ${ERROR_COLOR}$1${RESET}"\n"

# Rules
release: all-external-pushes

test-release: docker-test-repo-push

all-external-pushes: twine-upload docker-push source-code-release-push

docker-push twine-upload source-code-release-push: .all-credentials-available source-code-main-push

docker-test-repo-push: .docker-credentials-available

.all-credentials-available: .pypi-credentials-available .docker-credentials-available
	@touch .all-credentials-available

.pypi-credentials-available:
	@printf $(call color_in_progress,'Searching ~/.pypirc for PyPI credentials')
	@date +%s > current_time.txt
	@if [[ "${PYPI_CREDENTIALS}" == "'found'" ]]; \
    then \
        initial=$$(cat current_time.txt); rm current_time.txt; now_secs=$$(date +%s); \
        ((transpired=now_secs - initial)); \
        printf $(call color_final,'Found.',$$transpired"s") ; \
        touch .pypi-credentials-available; \
    else \
        printf $(call color_error,'Not found.') ; \
        exit 1; \
    fi;

.docker-credentials-available:
	@printf $(call color_in_progress,'Searching ~/.docker/config.json for docker credentials')
	@date +%s > current_time.txt
	@if [[ "${DOCKER_CREDENTIALS}" == "'found'" ]]; \
    then  \
        initial=$$(cat current_time.txt); rm current_time.txt; now_secs=$$(date +%s); \
        ((transpired=now_secs - initial)); \
        printf $(call color_final,'Found.',$$transpired"s") ; \
        touch .docker-credentials-available; \
    else \
        printf $(call color_error,'Not found.') ; \
        exit 1; \
    fi;

docker-push: docker-build
	@version=$$(cat ${VERSION_FILE}) ;\
	docker push ${DOCKER_ORG_NAME}/${DOCKER_REPO}:$$version
	@docker push ${DOCKER_ORG_NAME}/${DOCKER_REPO}:latest

docker-build: Dockerfile .controlled-source-files-unchanged .commit-new-version
	@printf $(call color_in_progress,'Building Docker container')
	@date +%s > current_time.txt
	@version=$$(cat ${VERSION_FILE}) ;\
	docker build -t ${DOCKER_ORG_NAME}/${DOCKER_REPO}:$$version -t ${DOCKER_ORG_NAME}/${DOCKER_REPO}:latest . >/dev/null 2>&1
	@initial=$$(cat current_time.txt); rm current_time.txt; now_secs=$$(date +%s); \
    ((transpired=now_secs - initial)); \
    printf $(call color_final,'Built.',$$transpired"s")

docker-test-repo-push: docker-test-build
	@version=$$(cat ${VERSION_FILE}) ;\
	docker push ${DOCKER_ORG_NAME}/${DOCKER_TEST_REPO}:$$version
	@docker push ${DOCKER_ORG_NAME}/${DOCKER_TEST_REPO}:latest

docker-test-build: Dockerfile .controlled-source-files-unchanged
	@printf $(call color_in_progress,'Building Docker container (for upload to test repository)')
	@date +%s > current_time.txt
	@version=$$(cat ${VERSION_FILE}) ;\
	docker build -t ${DOCKER_ORG_NAME}/${DOCKER_TEST_REPO}:$$version -t ${DOCKER_ORG_NAME}/${DOCKER_TEST_REPO}:latest . >/dev/null 2>&1
	@initial=$$(cat current_time.txt); rm current_time.txt; now_secs=$$(date +%s); \
    ((transpired=now_secs - initial)); \
    printf $(call color_final,'Built.',$$transpired"s")

Dockerfile: ${BIN}/Dockerfile.template ${LIBRARY_METADATA} ${BIN}/sed_wrapper.sh
	@printf $(call color_in_progress,'Generating Dockerfile')
	@date +%s > current_time.txt
	@sed "s/^/RUN pip install --no-cache-dir /g" requirements.txt > requirements_docker.txt
	@line_number=$$(grep -n '{{install requirements.txt}}' building/Dockerfile.template | cut -d ":" -f 1); \
    { head -n $$(($$line_number-1)) building/Dockerfile.template; cat requirements_docker.txt; tail -n +$$line_number building/Dockerfile.template; } > Dockerfile
	@rm requirements_docker.txt
	@version=$$(cat ${VERSION_FILE}) ;\
	source ${BIN}/sed_wrapper.sh; sed_i_wrapper -i "s/{{version}}/$$version/g" Dockerfile
	@source ${BIN}/sed_wrapper.sh; sed_i_wrapper -i "s/{{install requirements.txt}}//g" Dockerfile
	@initial=$$(cat current_time.txt); rm current_time.txt; now_secs=$$(date +%s); \
    ((transpired=now_secs - initial)); \
    printf $(call color_final,'Generated.',$$transpired"s")

twine-upload: .package-build
	@${PYTHON} -m twine upload --repository spatialprofilingtoolbox dist/*

source-code-release-push: .on-main-branch
	@git checkout ${RELEASE_TO_BRANCH} >/dev/null 2>&1
	@git merge main >/dev/null 2>&1
	@git push >/dev/null 2>&1
	@git checkout main >/dev/null 2>&1

source-code-main-push: .test .commit-new-version
	@git push >/dev/null 2>&1
	@version=$$(cat ${VERSION_FILE}) ;\
	git push origin v$$version >/dev/null 2>&1

.test: .unit-tests ${INTEGRATION_TESTS}
	@touch .test

.unit-tests: .installed-in-venv ${UNIT_TEST_SOURCES}
	@printf $(call color_in_progress,'Doing unit tests')
	@date +%s > current_time.txt
	@outcome=$$(cd tests/; source ../venv/bin/activate; python -m pytest -q . | tail -n1 | grep "[0-9]\+ \${LEFT_PAREN}failed\|errors\${RIGHT_PAREN}" ); \
    if [[ "$$outcome" != "" ]]; \
    then \
        source venv/bin/activate; \
        cd tests/; \
        python -m pytest; \
        printf $(call color_error,'Something went wrong in unit tests.'); \
        cd ../; \
        deactivate; \
        exit 1; \
    fi; \
    cd ../
	@initial=$$(cat current_time.txt); rm current_time.txt; now_secs=$$(date +%s); \
    ((transpired=now_secs - initial)); \
    printf $(call color_final,'Passed.',$$transpired"s")
	@touch .unit-tests

${INTEGRATION_TESTS} : .nextflow-available .installed-in-venv ${INTEGRATION_TEST_SOURCES}
	@script=$$(echo $@ | sed 's/^\.//g'); printf $(call color_in_progress,'Integration test '$@)
	@date +%s > current_time.txt
	@script=$$(echo $@ | sed 's/^\.//g'); \
    source venv/bin/activate; \
    cd tests/; \
    ./integration_tests/$$script >/dev/null 2>&1
	@initial=$$(cat current_time.txt); rm current_time.txt; now_secs=$$(date +%s); \
    ((transpired=now_secs - initial)); \
    printf $(call color_final,'Passed.',$$transpired"s")

.nextflow-available:
	@printf $(call color_in_progress,'Searching for Nextflow installation')
	@if [[ "${NEXTFLOW}" == "" ]]; \
    then \
        printf $(call color_error,'You need to install nextflow.') ; \
        exit 1; \
    fi; \
    touch .nextflow-available;\
    ((transpired=now_secs - initial)); \
	printf $(call color_final,${NEXTFLOW},$$transpired"s")

.installed-in-venv: .package-build
	@printf $(call color_in_progress,'Creating venv')
	@date +%s > current_time.txt
	@${PYTHON} -m venv venv
	@initial=$$(cat current_time.txt); rm current_time.txt; now_secs=$$(date +%s); \
    ((transpired=now_secs - initial)); \
    printf $(call color_final,'Created.',$$transpired"s")
	@printf $(call color_in_progress,'Installing spatialprofilingtoolbox into venv')
	@date +%s > current_time.txt
	@source venv/bin/activate ; \
    for wheel in dist/*.whl; \
    do \
        pip install $$wheel >/dev/null 2>&1; \
    done; \
    pip install pytest >/dev/null 2>&1;
	@touch .installed-in-venv
	@initial=$$(cat current_time.txt); rm current_time.txt; now_secs=$$(date +%s); \
    ((transpired=now_secs - initial)); \
    printf $(call color_final,'Installed.',$$transpired"s")

.commit-new-version: .update-version .package-build
	@printf $(call color_in_progress,'Committing source')
	@date +%s > current_time.txt
	@git add ${VERSION_FILE} >/dev/null 2>&1
	@version=$$(cat ${VERSION_FILE}) ;\
    git commit -m "Autoreleasing v$$version" >/dev/null 2>&1
	@version=$$(cat ${VERSION_FILE}) ;\
    git tag v$$version >/dev/null 2>&1
	@touch .commit-new-version
	@initial=$$(cat current_time.txt); rm current_time.txt; now_secs=$$(date +%s); \
    ((transpired=now_secs - initial)); \
    version=$$(cat ${VERSION_FILE}) ;\
    printf $(call color_final,'Committed.',$$transpired"s");

.update-version: .controlled-source-files-unchanged .on-main-branch
	@printf $(call color_in_progress,'Updating version')
	@date +%s > current_time.txt
	@if [[ "$$OSTYPE" == "darwin"* ]]; \
    then \
        version=$$(cat ${VERSION_FILE}) ;\
        prefix=$$(echo "$$version" | grep -o '^[0-9]\+\.[0-9]\+\.'); \
        microversion=$$(echo "$$version" | grep -o '[0-9]\+$$'); \
    else \
        version=$$(cat ${VERSION_FILE}) ;\
        prefix=$$(echo "$$version" | grep -oP '^([\d]+\.[\d]+\.)'); \
        microversion=$$(echo "$$version" | grep -oP '([\d]+)$$'); \
    fi; \
    microversion=$$(( microversion + 1 )); \
    echo -n "$$prefix$$microversion" > ${VERSION_FILE};
	@touch .update-version;
	@initial=$$(cat current_time.txt); rm current_time.txt; now_secs=$$(date +%s); \
    ((transpired=now_secs - initial)); \
    printf $(call color_final,'Updated.',$$transpired"s");

.controlled-source-files-unchanged:
	@if [[ "$$(${BIN}/check_commit_state.sh)" == "yes" ]]; \
    then \
        printf $(call color_error,'Start with a clean repository.'); \
        exit 1; \
    fi
	@touch .controlled-source-files-unchanged

.on-main-branch:
	@BRANCH=$$(git status | head -n1 | sed 's/On branch //g'); \
    if [[ $$BRANCH != "main" ]]; \
    then \
        printf $(call color_error,"Do release actions from the main branch (not $$BRANCH)."); \
        exit 1; \
    fi
	@touch .on-main-branch

.package-build: ${LIBRARY_SOURCES} ${LIBRARY_METADATA}
	@printf $(call color_in_progress,'Building spatialprofilingtoolbox')
	@date +%s > current_time.txt
	@${PYTHON} -m build 1>/dev/null
	@touch .package-build
	@initial=$$(cat current_time.txt); rm current_time.txt; now_secs=$$(date +%s); \
    ((transpired=now_secs - initial)); \
    printf $(call color_final,"Built.",$$transpired"s")

clean: clean-tests
	@rm -f ${PLACEHOLDERS}
	@rm -f Dockerfile
	@rm -rf dist/
	@rm -rf build/
	@rm -rf spatialprofilingtoolbox.egg-info/
	@rm -rf docs/_build/
	@rm -rf venv/
	@rm -rf current_time.txt

clean-tests:
	@rm -f tests/.nextflow.log*
	@rm -rf tests/.nextflow
	@rm -rf tests/work
	@rm -rf tests/results
	@rm -f tests/.spt_pipeline.json
	@rm -f tests/spt_pipeline.nf
	@rm -f tests/nextflow.config.lsf
	@rm -f tests/nextflow.config.local
	@rm -rf tests/unit_tests/__pycache__/
	@rm -rf tests/normalized_source_data.db
	@rm -rf tests/example_merged.db
