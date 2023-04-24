# Set up makefile config
.RECIPEPREFIX = >
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules
# export

# Define globally used variables
# Locations are relative unless indicated otherwise
PACKAGE_NAME := spatialprofilingtoolbox
export PYTHON := python
export BUILD_SCRIPTS_LOCATION_ABSOLUTE := ${PWD}/build/build_scripts
SOURCE_LOCATION := ${PACKAGE_NAME}
BUILD_LOCATION := build
BUILD_LOCATION_ABSOLUTE := ${PWD}/build
export TEST_LOCATION := test
export TEST_LOCATION_ABSOLUTE := ${PWD}/${TEST_LOCATION}
LOCAL_USERID := $(shell id -u)
VERSION := $(shell cat pyproject.toml | grep version | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
export WHEEL_FILENAME := ${PACKAGE_NAME}-${VERSION}-py3-none-any.whl
export MESSAGE := bash ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/verbose_command_wrapper.sh

help:
>@${MESSAGE} print ' The main targets are:'
>@${MESSAGE} print '  '
>@${MESSAGE} print '      make release-package'
>@${MESSAGE} print '          Build the Python package wheel and push it to PyPI.'
>@${MESSAGE} print ' '
>@${MESSAGE} print '      make build-docker-images'
>@${MESSAGE} print '          Build the Docker images.'
>@${MESSAGE} print ' '
>@${MESSAGE} print '      make build-and-push-docker-images'
>@${MESSAGE} print '          Build the Docker images and push them to DockerHub repositories.'
>@${MESSAGE} print ' '
>@${MESSAGE} print '      make test'
>@${MESSAGE} print '          Do unit and module tests.'
>@${MESSAGE} print ' '
>@${MESSAGE} print '      make [unit | module]-test-[apiserver | cggnn | countsserver | db | workflow]'
>@${MESSAGE} print '          Do only the unit or module tests for the indicated module.'
>@${MESSAGE} print ' '
>@${MESSAGE} print '      make clean'
>@${MESSAGE} print '          Attempt to remove all build or partial-build artifacts.'
>@${MESSAGE} print ' '
>@${MESSAGE} print '      make clean-docker-images'
>@${MESSAGE} print '          Aggressively removes the Docker images created here.'
>@${MESSAGE} print '          It makes use `docker system prune`, which might delete other images, so use at your own risk.'
>@${MESSAGE} print '          This target does not attempt to remove external images pulled as base images, however.'
>@${MESSAGE} print '          Note that normal `make clean` does not attempt to remove Docker images at all.'
>@${MESSAGE} print ' '
>@${MESSAGE} print '      make help'
>@${MESSAGE} print '          Show this text.'
>@${MESSAGE} print ' '
>@${MESSAGE} print ' Use VERBOSE=1 to show command outputs.'
>@${MESSAGE} print ' '

# Docker and test variables
export DOCKER_ORG_NAME := nadeemlab
export DOCKER_REPO_PREFIX := spt
DOCKERIZED_SUBMODULES := apiserver cggnn countsserver db workflow
DOCKERFILE_SOURCES := $(wildcard ${BUILD_LOCATION}/*/Dockerfile.*)
DOCKERFILE_TARGETS := $(foreach submodule,$(DOCKERIZED_SUBMODULES),${BUILD_LOCATION}/$(submodule)/Dockerfile)
DOCKER_BUILD_TARGETS := $(foreach submodule,$(DOCKERIZED_SUBMODULES),${BUILD_LOCATION_ABSOLUTE}/$(submodule)/docker.built)
DOCKER_PUSH_TARGETS := $(foreach submodule,$(DOCKERIZED_SUBMODULES),docker-push-${PACKAGE_NAME}/$(submodule))
DOCKER_PUSH_DEV_TARGETS := $(foreach submodule,$(DOCKERIZED_SUBMODULES),docker-push-dev-${PACKAGE_NAME}/$(submodule))
MODULE_TEST_TARGETS := $(foreach submodule,$(DOCKERIZED_SUBMODULES),module-test-$(submodule))
UNIT_TEST_TARGETS := $(foreach submodule,$(DOCKERIZED_SUBMODULES),unit-test-$(submodule))
DLI := force-rebuild-data-loaded-image

# Define PHONY targets
.PHONY: help release-package check-for-pypi-credentials print-source-files build-and-push-docker-images ${DOCKER_PUSH_TARGETS} build-docker-images test module-tests ${MODULE_TEST_TARGETS} ${UNIT_TEST_TARGETS} clean clean-files docker-compositions-rm clean-network-environment

# Submodule-specific variables
export DB_SOURCE_LOCATION_ABSOLUTE := ${PWD}/${SOURCE_LOCATION}/db
export DB_BUILD_LOCATION_ABSOLUTE := ${PWD}/${BUILD_LOCATION}/db
# Locations can't be relative because these are used by the submodules' Makefiles.

# Fetch all runnable files that will be needed for making
PACKAGE_SOURCE_FILES := pyproject.toml $(shell find ${SOURCE_LOCATION} -type f)

# Redefine what shell to pass to submodule makefiles
export SHELL := ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/status_messages_only_shell.sh

# Adjust verbosity based on how make was called
ifdef VERBOSE
export .SHELLFLAGS := -c -super-verbose
else
export .SHELLFLAGS := -c -not-super-verbose
endif

release-package: development-image check-for-pypi-credentials
>@${MESSAGE} start "Uploading spatialprofilingtoolbox==${VERSION} to PyPI"
>@cp ~/.pypirc .
>@docker run -u ${LOCAL_USERID} --rm --mount type=bind,src=${PWD},dst=/mount_sources -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest /bin/bash -c 'cd /mount_sources; PYTHONDONTWRITEBYTECODE=1 python -m twine upload --config-file .pypirc --repository ${PACKAGE_NAME} dist/${WHEEL_FILENAME} ' ; echo "$$?" > status_code
>@${MESSAGE} end "Uploaded." "Error."
>@rm -f .pypirc

check-for-pypi-credentials:
>@${MESSAGE} start "Checking for PyPI credentials in ~/.pypirc for spatialprofilingtoolbox"
>@${PYTHON} ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/check_for_credentials.py pypi ; echo "$$?" > status_code
>@${MESSAGE} end "Found." "Not found."

development-image: ${PACKAGE_SOURCE_FILES} ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/development.Dockerfile
>@${MESSAGE} start "Building development image"
>@cp ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/.dockerignore . 
>@docker build \
     --rm \
     -f ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/development.Dockerfile \
     -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
     --build-arg WHEEL_FILENAME=$${WHEEL_FILENAME} \
     . ; echo "$$?" > status_code ; \
    status_code=$$(cat status_code) ; \
    if [[ "$$status_code" == "0" ]]; \
    then \
        if [ ! -d dist/ ]; then mkdir dist ; fi; \
        docker run --rm -v $$(pwd)/dist:/buffer ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development /bin/sh -c "cp dist/${WHEEL_FILENAME} /buffer; chown ${LOCAL_USERID}:${LOCAL_USERID} /buffer/*; "; \
    fi 
>@status_code=$$(cat status_code); \
    if [[ "$$status_code" == "0" ]]; \
    then \
        touch development-image ; \
    fi
>@${MESSAGE} end "Built." "Build failed."
>@rm -f .dockerignore

print-source-files:
>@echo "${PACKAGE_SOURCE_FILES}" | tr ' ' '\n'

build-and-push-docker-images: ${DOCKER_PUSH_TARGETS}

build-and-push-docker-images-dev: ${DOCKER_PUSH_DEV_TARGETS}

${DOCKER_PUSH_TARGETS}: build-docker-images check-for-docker-credentials
>@submodule_directory=$$(echo $@ | sed 's/^docker-push-//g') ; \
    submodule_version=$$(grep '^__version__ = ' $$submodule_directory/__init__.py |  grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') ;\
    submodule_name=$$(echo $$submodule_directory | sed 's/spatialprofilingtoolbox\///g') ; \
    repository_name=${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-$$submodule_name ; \
    ${MESSAGE} start "Pushing Docker container $$repository_name"
>@submodule_directory=$$(echo $@ | sed 's/^docker-push-//g') ; \
    submodule_version=$$(grep '^__version__ = ' $$submodule_directory/__init__.py |  grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') ;\
    echo "$$submodule_version"; \
    submodule_name=$$(echo $$submodule_directory | sed 's/spatialprofilingtoolbox\///g') ; \
    echo "$$submodule_name"; \
    repository_name=${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-$$submodule_name ; \
    echo "$$repository_name"; \
    docker push $$repository_name:$$submodule_version ; \
    exit_code1=$$?; \
    docker push $$repository_name:latest ; \
    exit_code2=$$?; \
    exit_code=$$(( exit_code1 + exit_code2 )); echo "$$exit_code" > status_code
>@${MESSAGE} end "Pushed." "Not pushed."

${DOCKER_PUSH_DEV_TARGETS}: build-docker-images check-for-docker-credentials
>@submodule_directory=$$(echo $@ | sed 's/^docker-push-dev-//g') ; \
    submodule_version=$$(grep '^__version__ = ' $$submodule_directory/__init__.py |  grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') ;\
    submodule_name=$$(echo $$submodule_directory | sed 's/spatialprofilingtoolbox\///g') ; \
    repository_name=${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-$$submodule_name ; \
    ${MESSAGE} start "Pushing Docker container $$repository_name"
>@submodule_directory=$$(echo $@ | sed 's/^docker-push-dev-//g') ; \
    submodule_version=$$(grep '^__version__ = ' $$submodule_directory/__init__.py |  grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') ;\
    echo "$$submodule_version"; \
    submodule_name=$$(echo $$submodule_directory | sed 's/spatialprofilingtoolbox\///g') ; \
    echo "$$submodule_name"; \
    repository_name=${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-$$submodule_name ; \
    echo "$$repository_name"; \
    docker push $$repository_name:dev ; \
    exit_code1=$$?; \
    echo "$$exit_code1" > status_code
>@${MESSAGE} end "Pushed." "Not pushed."

check-for-docker-credentials:
>@${MESSAGE} start "Checking for Docker credentials in ~/.docker/config.json"
>@${PYTHON} ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/check_for_credentials.py docker ; status="$$?"; echo "$$status" > status_code; if [[ "$$status" == "0" ]]; then touch check-for-docker-credentials; fi;
>@${MESSAGE} end "Found." "Not found."

build-docker-images: ${DOCKER_BUILD_TARGETS}

# Build the Docker container for each submodule by doing the following:
#   0. Make the Dockerfiles for all submodules
#   1. Identify the submodule being built
#   2. Emit a message about it
#   3. Copy relevant files to the build folder
#   4. docker build the container
#   5. Remove copied files
${DOCKER_BUILD_TARGETS}: ${DOCKERFILE_TARGETS} development-image check-docker-daemon-running check-for-docker-credentials
>@submodule_directory=$$(echo $@ | sed 's/\/docker.built//g') ; \
    dockerfile=$${submodule_directory}/Dockerfile ; \
    submodule_name=$$(echo $$submodule_directory | sed 's,${BUILD_LOCATION_ABSOLUTE}\/,,g') ; \
    submodule_version=$$(grep '^__version__ = ' ${SOURCE_LOCATION}/$$submodule_name/__init__.py |  grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') ;\
    repository_name=${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-$$submodule_name ; \
    ${MESSAGE} start "Building Docker image $$repository_name"
>@submodule_directory=$$(echo $@ | sed 's/\/docker.built//g') ; \
    dockerfile=$${submodule_directory}/Dockerfile ; \
    submodule_name=$$(echo $$submodule_directory | sed 's,${BUILD_LOCATION_ABSOLUTE}\/,,g') ; \
    submodule_version=$$(grep '^__version__ = ' ${SOURCE_LOCATION}/$$submodule_name/__init__.py |  grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') ;\
    repository_name=${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-$$submodule_name ; \
    cp dist/${WHEEL_FILENAME} $$submodule_directory ; \
    cp $$submodule_directory/Dockerfile ./Dockerfile ; \
    cp ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/.dockerignore . ; \
    if [ ! -f $$submodule_directory/requirements.txt ]; then bash ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/create_requirements.sh > $$submodule_directory/requirements.txt ; fi; \
    if [ ! -f $$submodule_directory/specific_requirements.txt ]; then bash ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/create_requirements.sh $$submodule_name > $$submodule_directory/specific_requirements.txt ; fi; \
    docker build \
     -f ./Dockerfile \
     -t $$repository_name:$$submodule_version \
     -t $$repository_name:latest \
     -t $$repository_name:dev \
     --build-arg version=$$submodule_version \
     --build-arg service_name=$$submodule_name \
     --build-arg WHEEL_FILENAME=$${WHEEL_FILENAME} \
     $$submodule_directory ; echo "$$?" > status_code; \
    if [[ "$$(cat status_code)" == "0" ]]; \
    then \
        touch $@ ;\
    fi
>@${MESSAGE} end "Built." "Build failed."
>@submodule_directory=$$(echo $@ | sed 's/\/docker.built//g') ; \
    rm $$submodule_directory/${WHEEL_FILENAME} ; \
    rm ./Dockerfile ; \
    rm ./.dockerignore ; \

# Assemble the Dockerfile for the submodule using either
#   1. Dockerfile.base and [submodule]/Dockerfile.append, or
#   2. [submodule]/Dockerfile.template 
${DOCKERFILE_TARGETS}: development-image ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/Dockerfile.base ${DOCKERFILE_SOURCES}
>@submodule_directory=$$(echo $@ | sed 's/Dockerfile//g' ) ; \
    ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory Dockerfile

check-docker-daemon-running:
>@${MESSAGE} start "Checking that Docker daemon is running"
>@docker stats --no-stream ; echo "$$?" > status_code
>@${MESSAGE} end "Running." "Not running."
>@status_code=$$(cat status_code); \
    if [ $$status_code -gt 0 ] ; \
    then \
        ${MESSAGE} start "Attempting to start Docker daemon" ; \
        bash ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/start_docker_daemon.sh ; echo "$$?" > status_code ; \
        status_code=$$(cat status_code); \
        if [ $$status_code -eq 1 ] ; \
        then \
            ${MESSAGE} end "--" "Timed out." ; \
        else \
            ${MESSAGE} end "Started." "Failed to start." ; \
        fi ; \
    fi ; \
    touch check-docker-daemon-running

.initial_time.txt:
>@date +%s > .initial_time.txt

test: unit-tests module-tests
>@${MESSAGE} start " "
>@cp .initial_time.txt .current_time.txt; \
    rm .initial_time.txt; \
    ${MESSAGE} end "Total time:" "Error computing time."

module-tests: ${MODULE_TEST_TARGETS}

${MODULE_TEST_TARGETS}: development-image data-loaded-image-1small data-loaded-image-1 data-loaded-image-1and2 ${DOCKER_BUILD_TARGETS} clean-network-environment .initial_time.txt
>@submodule_directory=$$(echo $@ | sed 's/^module-test-/${BUILD_LOCATION}\//g') ; \
    ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory module-tests ;

unit-tests: ${UNIT_TEST_TARGETS}

${UNIT_TEST_TARGETS}: development-image data-loaded-image-1small data-loaded-image-1 data-loaded-image-1and2 ${DOCKER_BUILD_TARGETS} clean-network-environment .initial_time.txt
>@submodule_directory=$$(echo $@ | sed 's/^unit-test-/${BUILD_LOCATION}\//g') ; \
    ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory unit-tests ;

# The below explicitly checks whether the docker image already exists locally.
# If so, not rebuilt. To trigger rebuild, use "make clean-docker-images" first.
data-loaded-image-%: ${BUILD_LOCATION_ABSOLUTE}/db/docker.built ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/import_test_dataset%.sh
>@${MESSAGE} start "Building test-data-loaded spt-db image ($*)"
>@cp ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/.dockerignore . 
>@source ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/check_image_exists.sh; \
    exists=$$(check_image_exists ${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-db-preloaded-$*); \
    if [[ "$$exists" == "no" ]]; \
    then \
        docker container create --name temporary-spt-db-preloading --network host -e POSTGRES_PASSWORD=postgres -e PGDATA=.postgres/pgdata ${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-db:latest ; \
        docker container start temporary-spt-db-preloading && \
        bash ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/poll_container_readiness_direct.sh temporary-spt-db-preloading && \
        pipeline_cmd="cd /working_dir; cp -r /mount_sources/build .; cp -r /mount_sources/test .; bash build/build_scripts/import_test_dataset$*.sh "; \
        docker run \
        --rm \
        --network container:temporary-spt-db-preloading \
        --mount type=bind,src=${PWD},dst=/mount_sources \
        --mount type=tmpfs,destination=/working_dir \
        -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
        /bin/bash -c \
        "$$pipeline_cmd" ; echo "$$?" > status_code && \
        docker commit temporary-spt-db-preloading ${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-db-preloaded-$*:latest && \
        docker container rm --force temporary-spt-db-preloading ; \
    fi
>@status_code=$$(cat status_code); \
    if [[ "$$status_code" == "0" ]]; \
    then \
        touch data-loaded-image-$* ; \
    fi
>@${MESSAGE} end "Built." "Build failed."
>@rm -f .dockerignore

force-rebuild-data-loaded-images: ${DLI}-1 ${DLI}-2 ${DLI}-1and2 ${DLI}-1small

force-rebuild-data-loaded-image-%: ${BUILD_LOCATION_ABSOLUTE}/db/docker.built ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/import_test_dataset%.sh
>@${MESSAGE} start "Rebuilding test-data-loaded spt-db image ($*)"
>@cp ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/.dockerignore . 
>@source ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/check_image_exists.sh; \
    docker container create --name temporary-spt-db-preloading --network host -e POSTGRES_PASSWORD=postgres -e PGDATA=.postgres/pgdata ${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-db:latest ; \
    docker container start temporary-spt-db-preloading && \
    bash ${BUILD_SCRIPTS_LOCATION_ABSOLUTE}/poll_container_readiness_direct.sh temporary-spt-db-preloading && \
    pipeline_cmd="cd /working_dir; cp -r /mount_sources/build .; cp -r /mount_sources/test .; bash build/build_scripts/import_test_dataset$*.sh "; \
    docker run \
    --rm \
    --network container:temporary-spt-db-preloading \
    --mount type=bind,src=${PWD},dst=/mount_sources \
    --mount type=tmpfs,destination=/working_dir \
    -t ${DOCKER_ORG_NAME}-development/${DOCKER_REPO_PREFIX}-development:latest \
    /bin/bash -c \
    "$$pipeline_cmd" ; echo "$$?" > status_code && \
    docker commit temporary-spt-db-preloading ${DOCKER_ORG_NAME}/${DOCKER_REPO_PREFIX}-db-preloaded-$*:latest && \
    docker container rm --force temporary-spt-db-preloading ;
>@status_code=$$(cat status_code); \
    if [[ "$$status_code" == "0" ]]; \
    then \
        touch data-loaded-image-$* ; \
    fi
>@${MESSAGE} end "Rebuilt." "Rebuild failed."
>@rm -f .dockerignore

clean: clean-files clean-network-environment

clean-files:
>@rm -rf ${PACKAGE_NAME}.egg-info/
>@rm -rf dist/
>@rm -f .initiation_message_size
>@rm -f .current_time.txt
>@rm -f .initial_time.txt
>@rm -f ${BUILD_LOCATION}/*/.initiation_message_size
>@rm -f ${BUILD_LOCATION}/*/.current_time.txt
>@for submodule in ${DOCKERIZED_SUBMODULES} ; do \
        submodule_directory=${BUILD_LOCATION}/$$submodule ; \
        ${MAKE} SHELL=$(SHELL) --no-print-directory -C $$submodule_directory clean ; \
        rm -rf $$submodule_directory/docker.built ; \
    done
>@rm -f Dockerfile
>@rm -f .dockerignore
>@rm -rf spatialprofilingtoolbox.egg-info/
>@rm -rf __pycache__/
>@rm -f development-image
>@rm -f data-loaded-image-1
>@rm -f data-loaded-image-2
>@rm -f data-loaded-image-1and2
>@rm -f data-loaded-image-1small
>@rm -f .nextflow.log; rm -f .nextflow.log.*; rm -rf .nextflow/; rm -f configure.sh; rm -f run.sh; rm -f main.nf; rm -f nextflow.config; rm -rf work/; rm -rf results/
>@rm -f status_code
>@rm -f check-docker-daemon-running
>@rm -f check-for-docker-credentials
>@rm -rf ${BUILD_LOCATION}/lib
>@rm -f log_of_build.log
>@rm -f build/*/log_of_build.log

docker-compositions-rm: check-docker-daemon-running
>@${MESSAGE} start "Running docker compose rm (remove)"
>@docker compose --project-directory ./build/apiserver/ rm --force --stop ; status_code1="$$?" ; \
    docker compose --project-directory ./build/cggnn/ rm --force --stop ; status_code5="$$?" ; \
    docker compose --project-directory ./build/countsserver/ rm --force --stop ; status_code2="$$?" ; \
    docker compose --project-directory ./build/db/ rm --force --stop ; status_code3="$$?" ; \
    docker compose --project-directory ./build/workflow/ rm --force --stop ; status_code4="$$?" ; \
    status_code=$$(( status_code1 + status_code2 + status_code3 + status_code4 + status_code5 )) ; echo $$status_code > status_code
>@docker container rm --force temporary-spt-db-preloading
>@${MESSAGE} end "Down." "Error."

clean-network-environment: docker-compositions-rm

clean-docker-images:
>@docker system prune -f
>@for tag in $$(docker image ls | grep ${DOCKER_ORG_NAME} | awk '{print $$1":"$$2}'); \
    do \
    docker image rm $$tag; \
    done;
>@docker system prune -f
