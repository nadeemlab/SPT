
The modules in this repository are built, tested, and deployed using `make` and Docker.

| Development environment software requirements              | Version required or tested      |
| ---------------------------------------------------------- | ------------------------------- |
| Unix-like operating system                                 | Darwin 20.6.0 and Ubuntu 20.04  |
| [GNU Make](https://www.gnu.org/software/make/)             | 4.2.1                           |
| [Docker Engine](https://docs.docker.com/engine/install/)   | 20.10.17                        |
| [Docker Compose](https://docs.docker.com/compose/install/) | 2.10.2                          |
| [bash](https://www.gnu.org/software/bash/)                 | >= 4                            |
| [python](https://www.python.org/downloads/)                | >=3.7                           |

A typical development workflow looks like:

1. Modify or add source files.
2. Add new unit and "module" tests.
3. `$ make clean`
<pre>
Checking that Docker daemon is running <span style="color:olive;">...</span><span style="color:olive;">......................................</span> <span style="font-weight:bold;color:green;">Running.</span>       <span style="color:purple;">(1s)</span>
Running docker compose rm (remove) <span style="color:olive;">...</span><span style="color:olive;">..........................................</span> <span style="font-weight:bold;color:green;">Down.</span>          <span style="color:purple;">(1s)</span>
</pre>
4. `$ make test`
<pre>
Creating venv for basic package introspection <span style="color:olive;">...</span><span style="color:olive;">...............................</span> <span style="font-weight:bold;color:green;">Created.</span>       <span style="color:purple;">(5s)</span>
Creating spt CLI completions script <span style="color:olive;">...</span><span style="color:olive;">.........................................</span> <span style="font-weight:bold;color:green;">Created.</span>       <span style="color:purple;">(4s)</span>
Building development image <span style="color:olive;">...</span><span style="color:olive;">..................................................</span> <span style="font-weight:bold;color:green;">Built.</span>         <span style="color:purple;">(14s)</span>
Building apiserver Dockerfile <span style="color:olive;">...</span><span style="color:olive;">...............................................</span> <span style="font-weight:bold;color:green;">Built.</span>         <span style="color:purple;">(0s)</span>
Building countsserver Dockerfile <span style="color:olive;">...</span><span style="color:olive;">............................................</span> <span style="font-weight:bold;color:green;">Built.</span>         <span style="color:purple;">(0s)</span>
Building db Dockerfile <span style="color:olive;">...</span><span style="color:olive;">......................................................</span> <span style="font-weight:bold;color:green;">Built.</span>         <span style="color:purple;">(0s)</span>
Building workflow Dockerfile <span style="color:olive;">...</span><span style="color:olive;">................................................</span> <span style="font-weight:bold;color:green;">Built.</span>         <span style="color:purple;">(0s)</span>
Building Docker image nadeemlab/spt-db <span style="color:olive;">...</span><span style="color:olive;">......................................</span> <span style="font-weight:bold;color:green;">Built.</span>         <span style="color:purple;">(10s)</span>
Building test-data-loaded spt-db image <span style="color:olive;">...</span><span style="color:olive;">......................................</span> <span style="font-weight:bold;color:green;">Built.</span>         <span style="color:purple;">(18s)</span>
Building Docker image nadeemlab/spt-apiserver <span style="color:olive;">...</span><span style="color:olive;">...............................</span> <span style="font-weight:bold;color:green;">Built.</span>         <span style="color:purple;">(10s)</span>
Building Docker image nadeemlab/spt-countsserver <span style="color:olive;">...</span><span style="color:olive;">............................</span> <span style="font-weight:bold;color:green;">Built.</span>         <span style="color:purple;">(10s)</span>
Building Docker image nadeemlab/spt-workflow <span style="color:olive;">...</span><span style="color:olive;">................................</span> <span style="font-weight:bold;color:green;">Built.</span>         <span style="color:purple;">(10s)</span>
Running docker compose rm (remove) <span style="color:olive;">...</span><span style="color:olive;">..........................................</span> <span style="font-weight:bold;color:green;">Down.</span>          <span style="color:purple;">(1s)</span>
  testing environment (apiserver)  <span style="color:olive;">...</span><span style="color:olive;">..........................................</span> <span style="font-weight:bold;color:green;">Setup.</span>         <span style="color:purple;">(3s)</span>
    API internal basic database accessor <span style="color:olive;">...</span><span style="color:olive;">....................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(0s)</span>
  testing environment teardown <span style="color:olive;">...</span><span style="color:olive;">..............................................</span> <span style="font-weight:bold;color:green;">Down.</span>          <span style="color:purple;">(1s)</span>
  testing environment (countsserver)  <span style="color:olive;">...</span><span style="color:olive;">.......................................</span> <span style="font-weight:bold;color:green;">Setup.</span>         <span style="color:purple;">(1s)</span>
    binary expression viewer <span style="color:olive;">...</span><span style="color:olive;">................................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(1s)</span>
  testing environment teardown <span style="color:olive;">...</span><span style="color:olive;">..............................................</span> <span style="font-weight:bold;color:green;">Down.</span>          <span style="color:purple;">(0s)</span>
  testing environment (db)  <span style="color:olive;">...</span><span style="color:olive;">.................................................</span> <span style="font-weight:bold;color:green;">Setup.</span>         <span style="color:purple;">(2s)</span>
    guess channels from object files <span style="color:olive;">...</span><span style="color:olive;">........................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(1s)</span>
  testing environment teardown <span style="color:olive;">...</span><span style="color:olive;">..............................................</span> <span style="font-weight:bold;color:green;">Down.</span>          <span style="color:purple;">(0s)</span>
  testing environment (workflow)  <span style="color:olive;">...</span><span style="color:olive;">...........................................</span> <span style="font-weight:bold;color:green;">Setup.</span>         <span style="color:purple;">(2s)</span>
    signature cell set subsetting <span style="color:olive;">...</span><span style="color:olive;">...........................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(1s)</span>
  testing environment teardown <span style="color:olive;">...</span><span style="color:olive;">..............................................</span> <span style="font-weight:bold;color:green;">Down.</span>          <span style="color:purple;">(1s)</span>
  testing environment (apiserver)  <span style="color:olive;">...</span><span style="color:olive;">..........................................</span> <span style="font-weight:bold;color:green;">Setup.</span>         <span style="color:purple;">(2s)</span>
    single API route <span style="color:olive;">...</span><span style="color:olive;">........................................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(0s)</span>
    counts query delegation edge cases <span style="color:olive;">...</span><span style="color:olive;">......................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(1s)</span>
  testing environment teardown <span style="color:olive;">...</span><span style="color:olive;">..............................................</span> <span style="font-weight:bold;color:green;">Down.</span>          <span style="color:purple;">(1s)</span>
  testing environment (countsserver)  <span style="color:olive;">...</span><span style="color:olive;">.......................................</span> <span style="font-weight:bold;color:green;">Setup.</span>         <span style="color:purple;">(1s)</span>
    edge cases few markers <span style="color:olive;">...</span><span style="color:olive;">..................................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(1s)</span>
    single signature count query <span style="color:olive;">...</span><span style="color:olive;">............................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(0s)</span>
  testing environment teardown <span style="color:olive;">...</span><span style="color:olive;">..............................................</span> <span style="font-weight:bold;color:green;">Down.</span>          <span style="color:purple;">(1s)</span>
  testing environment (db)  <span style="color:olive;">...</span><span style="color:olive;">.................................................</span> <span style="font-weight:bold;color:green;">Setup.</span>         <span style="color:purple;">(1s)</span>
    basic health of database <span style="color:olive;">...</span><span style="color:olive;">................................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(1s)</span>
    drop recreate database constraints <span style="color:olive;">...</span><span style="color:olive;">......................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(3s)</span>
  testing environment teardown <span style="color:olive;">...</span><span style="color:olive;">..............................................</span> <span style="font-weight:bold;color:green;">Down.</span>          <span style="color:purple;">(0s)</span>
  testing environment (workflow)  <span style="color:olive;">...</span><span style="color:olive;">...........................................</span> <span style="font-weight:bold;color:green;">Setup.</span>         <span style="color:purple;">(2s)</span>
    proximity pipeline <span style="color:olive;">...</span><span style="color:olive;">......................................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(73s)</span>
  testing environment teardown <span style="color:olive;">...</span><span style="color:olive;">..............................................</span> <span style="font-weight:bold;color:green;">Down.</span>          <span style="color:purple;">(0s)</span>
</pre>

Optionally, if the images are ready to be released:

- `$ make build-and-push-docker-images`

<pre>
Checking for Docker credentials in ~/.docker/config.json <span style="color:olive;">...</span><span style="color:olive;">....................</span> <span style="font-weight:bold;color:green;">Found.</span>         <span style="color:purple;">(0s)</span>
Pushing Docker container nadeemlab/spt-apiserver <span style="color:olive;">...</span><span style="color:olive;">............................</span> <span style="font-weight:bold;color:green;">Pushed.</span>        <span style="color:purple;">(16s)</span>
Pushing Docker container nadeemlab/spt-countsserver <span style="color:olive;">...</span><span style="color:olive;">.........................</span> <span style="font-weight:bold;color:green;">Pushed.</span>        <span style="color:purple;">(15s)</span>
Pushing Docker container nadeemlab/spt-db <span style="color:olive;">...</span><span style="color:olive;">...................................</span> <span style="font-weight:bold;color:green;">Pushed.</span>        <span style="color:purple;">(23s)</span>
Pushing Docker container nadeemlab/spt-workflow <span style="color:olive;">...</span><span style="color:olive;">.............................</span> <span style="font-weight:bold;color:green;">Pushed.</span>        <span style="color:purple;">(27s)</span>
</pre>

If the package source code is ready to be released to PyPI:

- `$ make release-package`

<pre>
Checking for PyPI credentials in ~/.pypirc for spatialprofilingtoolbox <span style="color:olive;">...</span><span style="color:olive;">......</span> <span style="font-weight:bold;color:green;">Found.</span>         <span style="color:purple;">(0s)</span>
Uploading spatialprofilingtoolbox==0.11.0 to PyPI <span style="color:olive;">...</span><span style="color:olive;">...........................</span> <span style="font-weight:bold;color:green;">Found.</span>         <span style="color:purple;">(3s)</span>
</pre>

# Python package
There is one Python package, `spatialprofilingtoolbox`, containing all of the source code.

The package metadata uses the declarative `pyproject.toml` format.

# Modules
The main functionality is provided by 4 modules designed to operate as services. Each module's source is wrapped in a Docker image.

|                 |             |
| --------------- | ----------- |
| `apiserver`     | FastAPI application supporting queries over cell data. |
| `countsserver`  | An optimized class-counting program served by a custom TCP server. |
| `db`            | Data model/interface and PostgresQL database management SQL fragments. |
| `workflow`      | [Nextflow](https://www.nextflow.io)-orchestrated computation workflows. |

- *The `db` module is for testing only. A real PostgresQL database should generally not be deployed in a container.*

# Test-managed development
Test scripts are located under
- `spatialprofilingtoolbox/<module name>/unit_tests`
- `spatialprofilingtoolbox/<module name>/module_tests`

These tests serve multiple purposes for us:
1. To verify preserved functionality during source code modification.
2. To exemplify typical usage of classes and functions, including how they are wrapped in a container and how that container is setup.

# `spt` tab completion
Bash completion has been implemented that allows the user to readily assess and find functionality provided at the command line. This reduces the need for some kinds of documentation, since such documentation is already folded in to the executables in such a way that it can be readily accessed.

After installation of the Python package, an entry point `spt` is created. (Use `spt-enable-completion` to manually install the completion to a shell profile file).
- `spt [TAB]` yields the submodules which can be typed next.
- `spt <module name> [TAB]` yields the commands provided by the given module.
- `spt <module name> <command name> [TAB]` yields the `--help` text for the command.

For example:

```
$ spt [TAB]
countsserver  db  workflow

$ spt db [TAB]
create-schema  guess-channels-from-object-files  modify-constraints  status

$ spt db create-schema [TAB]
usage: spt db create-schema [-h] [--database-config-file DATABASE_CONFIG_FILE] [--force] [--refresh-views-only | --recreate-views-only]

Create scstudies database with defined schema.

optional arguments:
  -h, --help            show this help message and exit
  --database-config-file DATABASE_CONFIG_FILE
                        Provide the file for database configuration.
  --force               By default, tables are created only if they don't already exist. If "force" is set, all tables from the schema are dropped first. Obviously, use
                        with care; all data in existing tables will be deleted.
  --refresh-views-only  Only refresh materialized views, do not touch main table schema.
  --recreate-views-only
                        Only recreate views, do not touch main table schema.
```



