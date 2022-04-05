.help:
	#
	# This is mainly a lightweight release-management script for coordinated
	# DockerHub, GitHub, and PyPI releases of SPT (spatialprofilingtoolbox).
	#
	# The default target (achieved with "make") is
	#
	#     make release
	#
	# You can also use it for code testing:
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
.PHONY: (\
	release \
	all-external-pushes \
	twine-upload \
	docker-push \
	source-code-push \
	inform-credential-availability \
	committed-source \
	version-updated \
	clean \
)

# Functions
credentials_available = $(shell ${BIN}/check_for_credentials.py $1)
inform_of_availability = $(if $(filter 'found', $1),$(info $2),$(info $3))

# Run-time variables
PYPI_CREDENTIALS := $(call credentials_available,pypi)
DOCKER_CREDENTIALS := $(call credentials_available,docker)
GITHUB_CREDENTIALS := $(call credentials_available,github)
PLACEHOLDERS := .all-credentials-available .test .unit-tests .integration-tests

# Rules
release: all-external-pushes clean

all-external-pushes: twine-upload docker-push source-code-push

docker-push twine-upload source-code-push: all-credentials-available

.all-credentials-available:
	@if [[ $$PYPI_CREDENTIALS == "found" && $$DOCKER_CREDENTIALS == "found" && $$GITHUB_CREDENTIALS == "found" ]]; \
    then  \
        touch .all-credentials-available; \
    else \
    	echo "Some credentials not found."; \
    	exit 1; \
    fi;

version-updated:

inform-credential-availability:
	$(call inform_of_availability,${PYPI_CREDENTIALS},Found PyPI credentials at ~/.pypirc .,There are no usable PyPI credentials at ~/.pypirc .)
	$(call inform_of_availability,${DOCKER_CREDENTIALS},Found docker credentials at ~/.docker/config.json .,There are no usable docker credentials at ~/.docker/config.json .)
	$(call inform_of_availability,${GITHUB_CREDENTIALS},Found GitHub credentials satisfactory for write access to this repository.,Did not find GitHub credentials satisfactory for write access to this repository.)

committed-source:
	@echo 'cs'
	#check that git registers no changes except version

build:
	@echo 'bb'
	#check that git registers no changes except version

.unit-tests: build
	@touch .unit-tests

.nextflow-available:
	@touch .nextflow-available

.integration-tests: .nextflow-available
	@touch .integration-tests

.test: .unit-tests .integration-tests
	@touch .test

clean:
	@rm -f ${PLACEHOLDERS}

help: .help

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

