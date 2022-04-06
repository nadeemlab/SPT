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
BIN=${PWD}/building
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
	on-main-branch \
	repository-is-clean \
	no-other-changes \
	nextflow-available \
	clean \
)
RESET="\033[0m"
NOTE_COLOR="\033[0m"
NOTE_COLOR_FINAL="\033[32;1m"
ERROR_COLOR="\033[31;1m"
DOTS_COLOR="\033[33m"
PADDING=...............................................................
SPACE:=" "
COMMMA:=,

# Functions
credentials_available = $(shell ${BIN}/check_for_credentials.py $1)
color_in_progress = ${NOTE_COLOR}$1${SPACE}${DOTS_COLOR}$(shell padding="${PADDING}"; insertion="$1"; echo \"$${padding:$${\#insertion}}\"; )${RESET}" "
color_final = ${NOTE_COLOR_FINAL}$1${RESET}"\n"
color_error = ${ERROR_COLOR}$1${RESET}"\n"

# Run-time variables
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
PYTHON = python3

# Rules
release: all-external-pushes clean

test-release: docker-test-repo-push clean

all-external-pushes: twine-upload docker-push source-code-release-push

docker-push twine-upload source-code-release-push: .all-credentials-available source-code-main-push

docker-test-repo-push: .docker-credentials-available

.all-credentials-available: .pypi-credentials-available .docker-credentials-available
	@touch .all-credentials-available

.pypi-credentials-available:
	@printf $(call color_in_progress,'Searching ~/.pypirc for PyPI credentials')
	@if [[ "${PYPI_CREDENTIALS}" == "'found'" ]]; \
    then  \
        printf $(call color_final,'Found.') ; \
        touch .pypi-credentials-available; \
    else \
        printf $(call color_error,'Not found.') ; \
        exit 1; \
    fi;

docker-push: docker-build
	@printf $(call color_in_progress,'Pushing ${DOCKER_ORG_NAME}/${DOCKER_REPO}:${SPT_VERSION} \(also tagged latest\)')
	@docker push ${DOCKER_ORG_NAME}/${DOCKER_REPO}:${SPT_VERSION}
	@docker push ${DOCKER_ORG_NAME}/${DOCKER_REPO}:latest
	@printf $(call color_final,'Pushed.')

docker-build: Dockerfile repository-is-clean .commit-source-code
	@printf $(call color_in_progress,'Building Docker container')
	@docker build -t ${DOCKER_ORG_NAME}/${DOCKER_REPO}:${SPT_VERSION} -t ${DOCKER_ORG_NAME}/${DOCKER_REPO}:latest . >/dev/null 2>&1
	@printf $(call color_final,'Built.')

docker-test-repo-push: docker-test-build
	@printf $(call color_in_progress,'Pushing ${DOCKER_ORG_NAME}/${DOCKER_TEST_REPO}:${SPT_VERSION} \(also tagged latest\)')
	@docker push ${DOCKER_ORG_NAME}/${DOCKER_TEST_REPO}:${SPT_VERSION}
	@docker push ${DOCKER_ORG_NAME}/${DOCKER_TEST_REPO}:latest
	@printf $(call color_final,'Pushed.')

docker-test-build: Dockerfile repository-is-clean
	@printf $(call color_in_progress,'Building Docker container \(for upload to test repository\)')
	@docker build -t ${DOCKER_ORG_NAME}/${DOCKER_TEST_REPO}:${SPT_VERSION} -t ${DOCKER_ORG_NAME}/${DOCKER_TEST_REPO}:latest . >/dev/null 2>&1
	@printf $(call color_final,'Built.')

.docker-credentials-available:
	@printf $(call color_in_progress,'Searching ~/.docker/config.json for docker credentials')
	@if [[ "${DOCKER_CREDENTIALS}" == "'found'" ]]; \
    then  \
        printf $(call color_final,'Found.') ; \
        touch .docker-credentials-available; \
    else \
        printf $(call color_error,'Not found.') ; \
        exit 1; \
    fi;

Dockerfile: .version-updated
	@printf $(call color_in_progress,'Generating Dockerfile')
	@sed "s/^/RUN pip install --no-cache-dir /g" requirements.txt > requirements_docker.txt
	@line_number=$$(grep -n '{{install requirements.txt}}' building/Dockerfile.template | cut -d ":" -f 1); \
    { head -n $$(($$line_number-1)) building/Dockerfile.template; cat requirements_docker.txt; tail -n +$$line_number building/Dockerfile.template; } > Dockerfile
	@rm requirements_docker.txt
	@sed -i '' "s/{{version}}/${SPT_VERSION}/g" Dockerfile
	@sed -i '' "s/{{install requirements.txt}}//g" Dockerfile
	@printf $(call color_final,'Generated.')

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
        printf $(call color,'Do release actions from the main branch (not "$$BRANCH").'); \
        exit 1; \
    fi

twine-upload: .package-build

source-code-release-push:

source-code-main-push: .package-build

.test: .unit-tests .integration-tests
	@touch .test

.unit-tests: .installed-in-venv
	@touch .unit-tests

.integration-tests: nextflow-available .installed-in-venv
	@touch .integration-tests

nextflow-available:
	@$(info Nextflow entrypoint at: ${NEXTFLOW})
	@if [[ "${NEXTFLOW}" == "" ]]; \
    then \
        printf $(call color_error,'You need to install nextflow.') ; \
        exit 1; \
    fi

.installed-in-venv: .package-build
	@printf $(call color_in_progress,'Creating venv')
	@${PYTHON} -m venv venv;
	@printf $(call color_final,'Created.')
	@printf $(call color_in_progress,'Installing spatialprofilingtoolbox into venv')
	@source venv/bin/activate ; \
    for wheel in dist/*.whl; \
    do \
        pip install $$wheel 1>/dev/null 2>/dev/null; \
    done
	@touch .installed-in-venv
	@printf $(call color_final,'Installed.')

.package-build: dist/${WHEEL_NAME}
	@touch .package-build

dist/${WHEEL_NAME}:
	@printf $(call color_in_progress,'Building spatialprofilingtoolbox==${SPT_VERSION}')
	@${PYTHON} -m build 1>/dev/null
	@printf $(call color_final,'Built.')

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

