
Subpackages implementing finer-grained specific functionality.
Named with names matching a list of "extras" to appears in setup.py for the purpose of installing dependencies on a per-subpackage basis.
Then carefully arrange the imports and init files so that scripts from a given package do not import all other subpackages' dependencies.

## Subpackages
- control. Configuring runs, installing/setting up/status querying docker containers, reporting on log files.
- workflow. The components that are scheduled by the workflow manager/engine. Initializer, core, integrator, etc.
- db. DB administration tasks. Creating schema, constraints, views, granting roles, etc.
- countsserver. Cache builder, tcp server, client examples and benchmarking.
- apiserver. Containerized API server.
- dashboard. HTML/CSS/JS for frontend.

Each subpackage will have its own scripts and tests.

They will not need to be independently installable, however, so there is no need for the namespace package construct as far as I can tell.

The purpose of this degree of modularization is partly for staying organized during development, but it also has the practical function of reducing the time to load scripts which require only limited functionality. The import chain can otherwise be somewhat burdensome (e.g. if large figure-generating libraries are loaded for no reason, in a simple configuration utility).

## Makefiles
The make build system should be modularized accordingly. This will improve the maintenance of the currently quite large and monolithic Makefile.

## Docker
The subpackages workflows, countserver, and apiserver should support a uniform mechanism of Docker containerization, including convenience commands for pushing a new version to the Docker repository, and for pulling the images and starting the containers.

## Scripts
It would be nice for the extras feature of setuptools to also make installation of the scripts conditional on the extras. I don't think this is quite possible.

Instead perhaps a single "spt" CLI entrypoint can be defined, which looks up the correct script to run based on subsequent specifier keywords (as in e.g. "git mv").

Ideally this will come with a bash completion installation which allows tab completion to reveal installed commands, as in "spt conf[tab]" -> "spt configure" (or else list completions if more than one).

## Package metadata
It has been suggested in many places that setuptools and perhaps pip and other de facto standard Python tools are recommending deprecation of a setup.py in favor of a pyproject.toml.
The setuptools documentation has uniform switches to explain how to translate between setup.py, setup.cfg, and pyproject.toml.
Do this suggested migration as part of the modularization effort.

https://pip.pypa.io/en/stable/reference/build-system/pyproject-toml/

https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html



## Steps to accomplish the above

1. [DONE] Git move most existing files into the new directory structure, changing scripts to reflect new call syntax.
2. [DONE] Change all import statements to reflect new structure.
3. [DONE] Deprecate RTD docs.
4. [DONE] Do a first pass at resolving references to old file locations; tests, makefile, dockerfiles, setup.
5. [DONE] Write new entrypoint script "spt".
6. [DONE] Change invocations of the script files to reflect new entry point.
7. [DONE] Implement extras feature for submodules.
8. [DONE] Create bash completion spec and method of installation of it triggered by normal pip installation. Should be a single entry point with subsequent subpackage specifiers. At least one source just suggests adding to setup.py:setup():
    data_files=[
        ('/etc/bash_completion.d', ['extras/exampleprogram.completion']),
    ],
9. [DONE] Create manual completions install mechanism in case /etc/bash_completion.d does not exist.
10. [DONE] Remove explicit inclusion of schema artifacts, retreive from external package instead.
11. [DONE] Convert setup.py to pyproject.toml directives/items, reflecting the new structure.
12. [DONE] Learn how to do recursive make.
13. [DONE] Split off separate Makefiles in each module from the current Makefile, for things pertaining to that module.
14. Finish moving static file artifacts and modules into correct locations in new module structure.
15. Change tests to call correct scripts.
16. Create a Docker container around the DB.
17. Add mDNS for each service, simulating the service domain name resolution that will be performed in the actual orchestration case. For testing. Governed by an easy switch, to turn off in case of possible conflicts with real DNS.
18. Add utility commands e.g. for status, depending on the submodule.
19. Add actual unit tests (and module tests) and deprecate outdated tests.
20. Assess library dependency versions for a sharper version indicator, with less than / greater than.
21. Do complete revision of documentation to reflect changes. Include screenshots of latest UI, a short summary of functionality, a command reference, and a development/testing explanation section.

* [POSTPONE] In control module, add script to configure docker container with given repository/tag etc., to replace the bash scripts currently tailored to the api server.
* [POSTPONE] Create minimal K8S configuration for local development/testing.


## Moving altering directory
- [DONE] Consider each python module not in one of the submodules, try to push down.
- [DONE] (apiserver) Review contents, especially counts_service_client.
- [DONE] (apiserver) Review Dockerfile for needed partner service discovery environment variables.
- [DONE] (apiserver) Add healthcheck.
- [DONE] (apiserver) Document the API routes.
- [DONE] (apiserver) Create tests notes doc, proposing a few new tests.
- [DONE] (apiserver) Consider deprecation of deployment management subdirectory contents.
- [DONE] (apiserver) Create tests area. Structure: unit_tests, module_tests. (The term integration test will be reserved for higher-level involving multiple modules.)
- [DONE] (control) Review.
- [DONE] (control) Move configure to workflow.
- [DONE] (control) Consider factoring the control module out into other modules (if new utilities can also do this).
- [DONE] (countsserver) Review.
- [DONE] (countsserver) Health check.
- [DONE] (countsserver) Tests.
- [DONE] (countsserver) Tests ideas.
- [DONE] (countsserver) Deal with log_formats duplication.
- [SKIP] (countsserver) Add more control scripts (like stop). [Server pattern in container is to stop on container stop only]
- [SKIPPED] (dashboard) Skip for now, will be moved.
- (db) Review contents.
- (db) Create utilities notes doc, propose a few new utilities.
- (db) Write a note explaining decision regarding dockerization of this module.
- (db) Tests.
- (db) Test ideas.
- (entry_point) Add disable command.
- (test_data) Slim this down to only a modest sized dataset with the most updated formatting.
- (workflow) Review, especially environment for moving to a more general purpose module.
- (workflow) Bring templates together.
- (workflow) Dockerfile service discovery.
- (workflow) Possibly put nextflow into the container? To support a single-core use case.
- (workflow) Health check.
- (workflow) Tests.
- (workflow) Tests ideas.
- (workflow) More status utilities, possibly to replace or augment the detailed workflow logging.
- (workflow) Review init.


More notes
- Split off "view site" i.e. dashboard into new repository.

