
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

## Package metadata
It has been suggested in many places that setuptools and perhaps pip and other de facto standard Python tools are recommending deprecation of a setup.py in favor of a pyproject.toml.
The setuptools documentation has uniform switches to explain how to translate between setup.py, setup.cfg, and pyproject.toml.
Do this suggested migration as part of the modularization effort.

https://pip.pypa.io/en/stable/reference/build-system/pyproject-toml/

https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html



## Steps to accomplish the above

1. Git move most existing files into the new directory structure, changing scripts to reflect new call syntax.
2. Convert setup.py to pyproject.toml directives/items, reflecting the new structure.
3. Change all import statements to reflect new structure.
4. Create bash completion spec and method of installation of it triggered by normal pip installation. Should be a single entry point with subsequent subpackage specifiers. At least one source just suggests adding to setup.py:setup():
    data_files=[
        ('/etc/bash_completion.d', ['extras/exampleprogram.completion']),
    ],
5. In control module, add script to configure docker container with given repository/tag etc., to replace the bash scripts currently tailored to the api server.
6. Learn how to do recursive make.
7. Split off separate Makefiles in each module from the current Makefile, for things pertaining to that module.
8. Change tests to call correct scripts.

