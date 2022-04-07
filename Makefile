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
	# - Targets starting with '.' like '.all-credentials-available' (except
	#   '.help') create empty files that are placeholders indicating an
	#   environment or build state. They are all deleted on `make clean`, which
	#   you generally do not need to run manually. This usage is called "empty
	#   target files to record events" in the GNU Make documentation.
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
$(shell chmod +x tests/do_all_integration_tests.sh)
.PHONY: (\
	release \
	test-release \
	all-external-pushes \
	twine-upload \
	docker-push \
	docker-test-push \
	source-code-release-push \
	source-code-main-push \
	on-main-branch \
	repository-is-clean \
	no-other-changes \
	nextflow-available \
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

# Functions
credentials_available = $(shell ${BIN}/check_for_credentials.py $1)
color_in_progress = ${NOTE_COLOR}$1${SPACE}${DOTS_COLOR}$(shell padding="${PADDING}"; insertion="$1"; echo \"$${padding:$${\#insertion}}\"; )${RESET}" "
color_final = ${NOTE_COLOR_FINAL}$1${RESET}" "$(shell padding=..............................; insertion='$1'; echo \"$${padding:$${\#insertion}}\"; )" $2\n"
color_error = ${ERROR_COLOR}$1${RESET}"\n"

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
	.integration-tests \
	.commit-source-code \
	.version-updated \
	.installed-in-venv \
	.package-build
SPT_VERSION := $(shell cat spatialprofilingtoolbox/version.txt)
WHEEL_NAME := spatialprofilingtoolbox-${SPT_VERSION}-py3-none-any.whl
DOCKER_ORG_NAME := nadeemlab
DOCKER_REPO := spt
DOCKER_TEST_REPO := spt-test
PYTHON := python3
RELEASE_TO_BRANCH := prerelease

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
	@docker push ${DOCKER_ORG_NAME}/${DOCKER_REPO}:${SPT_VERSION}
	@docker push ${DOCKER_ORG_NAME}/${DOCKER_REPO}:latest

docker-build: Dockerfile repository-is-clean .commit-source-code
	@printf $(call color_in_progress,'Building Docker container')
	@date +%s > current_time.txt
	@docker build -t ${DOCKER_ORG_NAME}/${DOCKER_REPO}:${SPT_VERSION} -t ${DOCKER_ORG_NAME}/${DOCKER_REPO}:latest . >/dev/null 2>&1
	@initial=$$(cat current_time.txt); rm current_time.txt; now_secs=$$(date +%s); \
    ((transpired=now_secs - initial)); \
    printf $(call color_final,'Built.',$$transpired"s")

docker-test-repo-push: docker-test-build
	@docker push ${DOCKER_ORG_NAME}/${DOCKER_TEST_REPO}:${SPT_VERSION}
	@docker push ${DOCKER_ORG_NAME}/${DOCKER_TEST_REPO}:latest

docker-test-build: Dockerfile repository-is-clean
	@printf $(call color_in_progress,'Building Docker container (for upload to test repository)')
	@date +%s > current_time.txt
	@docker build -t ${DOCKER_ORG_NAME}/${DOCKER_TEST_REPO}:${SPT_VERSION} -t ${DOCKER_ORG_NAME}/${DOCKER_TEST_REPO}:latest . >/dev/null 2>&1
	@initial=$$(cat current_time.txt); rm current_time.txt; now_secs=$$(date +%s); \
    ((transpired=now_secs - initial)); \
    printf $(call color_final,'Built.',$$transpired"s")

Dockerfile: .version-updated
	@printf $(call color_in_progress,'Generating Dockerfile')
	@date +%s > current_time.txt
	@sed "s/^/RUN pip install --no-cache-dir /g" requirements.txt > requirements_docker.txt
	@line_number=$$(grep -n '{{install requirements.txt}}' building/Dockerfile.template | cut -d ":" -f 1); \
    { head -n $$(($$line_number-1)) building/Dockerfile.template; cat requirements_docker.txt; tail -n +$$line_number building/Dockerfile.template; } > Dockerfile
	@rm requirements_docker.txt
	@source ${BIN}/sed_wrapper.sh; sed_i_wrapper -i "s/{{version}}/${SPT_VERSION}/g" Dockerfile
	@source ${BIN}/sed_wrapper.sh; sed_i_wrapper -i "s/{{install requirements.txt}}//g" Dockerfile
	@initial=$$(cat current_time.txt); rm current_time.txt; now_secs=$$(date +%s); \
    ((transpired=now_secs - initial)); \
    printf $(call color_final,'Generated.',$$transpired"s")

.commit-source-code: repository-is-clean on-main-branch .package-build
	@git add spatialprofilingtoolbox/version.txt
	@git commit -m "Autoreleasing v${SPT_VERSION}"
	@git tag v${SPT_VERSION}
	@touch .commit-source-code

repository-is-clean: .version-updated no-other-changes

.version-updated:
	@if [[ "$$(${BIN}/check_commit_state.sh version-updated)" != "yes" ]]; \
    then \
        printf $(call color_error,'version.txt must be updated.'); \
        exit 1; \
    else \
        touch .version-updated; \
    fi

no-other-changes:
	@if [[ "$$(${BIN}/check_commit_state.sh something-else-updated)" == "yes" ]]; \
    then \
        printf $(call color_error,'Start with a clean repository${COMMA} with only a version.txt update.'); \
        exit 1; \
    fi

on-main-branch:
	@BRANCH=$$(git status | head -n1 | sed 's/On branch //g'); \
    if [[ $$BRANCH != "main" ]]; \
    then \
        printf $(call color_error,"Do release actions from the main branch (not $$BRANCH)."); \
        exit 1; \
    fi

twine-upload: .package-build
	@${PYTHON} -m twine upload --repository spatialprofilingtoolbox dist/*

source-code-release-push: on-main-branch
	@rm spatialprofilingtoolbox/version.txt
	@git checkout ${RELEASE_TO_BRANCH} >/dev/null 2>&1
	@git merge main >/dev/null 2>&1
	@git push >/dev/null 2>&1
	@git checkout main >/dev/null 2>&1

source-code-main-push: .package-build .commit-source-code
	@git push >/dev/null 2>&1
	@git push origin v${SPT_VERSION} >/dev/null 2>&1

.test: .unit-tests .integration-tests
	@touch .test

.unit-tests: .installed-in-venv
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

.integration-tests: nextflow-available .installed-in-venv
	@printf $(call color_in_progress,'Doing integration tests')
	@date +%s > current_time.txt
	@outcome=$$(cd tests/; source ../venv/bin/activate; ./do_all_integration_tests.sh | tail -n1 | grep "all [0-9]\+ SPT workflows integration tests passed in"); \
    if [[ "$$outcome" == "" ]]; \
    then \
        printf $(call color_error,'Something went wrong in integration tests.'); \
        exit 1; \
    fi
	@initial=$$(cat current_time.txt); rm current_time.txt; now_secs=$$(date +%s); \
    ((transpired=now_secs - initial)); \
    printf $(call color_final,'Passed.',$$transpired"s")
	@touch .integration-tests

nextflow-available:
	@printf $(call color_in_progress,'Searching for Nextflow installation')
	@if [[ "${NEXTFLOW}" == "" ]]; \
    then \
        printf $(call color_error,'You need to install nextflow.') ; \
        exit 1; \
    fi; \
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

.package-build: dist/${WHEEL_NAME}
	@touch .package-build

dist/${WHEEL_NAME}:
	@printf $(call color_in_progress,'Building spatialprofilingtoolbox==${SPT_VERSION}')
	@date +%s > current_time.txt
	@${PYTHON} -m build 1>/dev/null
	@initial=$$(cat current_time.txt); rm current_time.txt; now_secs=$$(date +%s); \
    ((transpired=now_secs - initial)); \
    printf $(call color_final,'Built.',$$transpired"s")

clean:
	@rm -f ${PLACEHOLDERS}
	@rm -f Dockerfile
	@rm -rf dist/
	@rm -rf build/
	@rm -rf spatialprofilingtoolbox.egg-info/
	@rm -rf docs/_build/
	@rm -f tests/.nextflow.log*
	@rm -rf tests/.nextflow
	@rm -rf tests/work
	@rm -rf tests/results
	@rm -f tests/.spt_pipeline.json
	@rm -f tests/spt_pipeline.nf
	@rm -f tests/nextflow.config.lsf
	@rm -f tests/nextflow.config.local
	@rm -rf venv/
	@rm -rf tests/unit_tests/__pycache__/

# Makefile migration

# Checks correct branch (main)
# Checks version.txt for update
# Checks that other git-controlled source files are *unchanged*
# Cleans previous dist/ artifacts
# Build wheels
# Start up venv
# Install built wheel into venv
# Install pytest into venv
# Unit testing in venv
# Integration tests in venv (also uses nextflow...)
# Some test artifact cleanup
# Create Docker file from template and version and requirements; depends on prod or test/dev
# Docker push (depends on credentials)
# Git add version and commit
# Git tag the version
# Git push
# Git merge into release/prerelease branch
# twine upload to PyPI (depends on credentials)

