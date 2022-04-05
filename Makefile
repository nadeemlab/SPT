SHELL = /bin/bash
.DELETE_ON_ERROR:

$(shell chmod +x building/check_for_credentials.py)

.PHONY: (\
	release \
	all-external-pushes \
	twine-upload \
	docker-push \
	source-code-push \
	committed-source \
	clean \
)

PLACEHOLDERS = .all-credentials-available .pypi-credentials-available .docker-credentials-available .git-credentials-available

release: all-external-pushes

all-external-pushes: twine-upload docker-push source-code-push

docker-push: .all-credentials-available

twine-upload: .all-credentials-available

source-code-push: .all-credentials-available twine-upload

.all-credentials-available: .pypi-credentials-available .docker-credentials-available .git-credentials-available

.pypi-credentials-available:
	@building/check_for_credentials.py pypi > outcome.txt; \
    if [[ "$$?" != "0" ]]; then exit 1; fi; \
    flag=$(cat outcome.txt); rm outcome.txt; \
    if [[ $$flag == "0" ]]; \
    then echo >&2 "There are no usable PyPI credentials at ~/.pypirc . )"; \
    exit 1; \
    else \
    echo >&2 "Found PyPI credentials at ~/.pypirc ."; \
    touch .pypi-credentials-available; \
    fi;

.docker-credentials-available:
	@building/check_for_credentials.py docker > outcome.txt; \
    if [[ "$$?" != "0" ]]; then exit 1; fi; \
    flag=$(cat outcome.txt); rm outcome.txt; \
    if [[ $$flag == "0" ]]; \
    then echo >&2 "There are no usable Docker credentials at ~/.docker/config.json . )"; \
    exit 1; \
    else \
    echo >&2 "Found Docker credentials at ~/.docker/config.json ."; \
    touch .docker-credentials-available; \
    fi;

.git-credentials-available:
	touch .git-credentials-available

# committed-source:
# 	check that git registers no changes except version

build:

.unit-tests: build
	touch .unit-tests

.nextflow-available:
	touch .nextflow-available

.integration-tests: .nextflow-available

.test: unit-tests integration-tests

clean:

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

