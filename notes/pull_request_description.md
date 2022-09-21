
This PR is a major refactoring intended to make the codebase more modular, testable, and deployable, and to make development tasks more efficient. It includes containerization into about 4 primary modules, a testing pattern at the unit and module level, factoring out the schema into a separate repository.

Previously the entire codebase was low-level "workflows", with a fairly robust modularity pattern supported by Nextflow orchestration. As new higher-level components (like the API server and web application) were added, an integration-enabling step like that undertaken in this PR became necessary.

# Updates

## Submodules

| submodule       | description |
| --------------- | ----------- |
| `apiserver`     | FastAPI application supporting queries over the cell data. |
| `countsserver`  | An optimized class-counting program served by a custom TCP server. |
| `db`            | Data model/interface and PostgresQL database management SQL fragments. |
| `workflow`      | The Nextflow-orchestrated computation workflows. |

There are also a few sibling directories that aren't exactly full-fledge modules: `entry_point` for the CLI, `standalone_utilities` for simple functionality common to several submodules, and `test_data`.

## Makefile improvements

The development tasks (Python packaging, building Docker images, testing) are organized with GNU Make. In this PR the previously monolithic Makefile has been distributed somewhat into submodules using recursive submake.

While `make` might seem to be an antiquated tool, it's relatively simple and widely available. Also, despite primary usage for C/C++ projects, it is ultimately designed for coordinating dependent tasks at the command line which largely depend on source files, which is what we are using it for.

This now includes:

- building virtual environments specially for each submodule
- 4 Docker images (one for each of the submodules listed above)
- automatic startup of the Docker engine
- Docker Compose for setting up test environments
- at least 1 unit test and 1 module test in each (sub)module, to establish the pattern of test implementation

## Test data environment

For testing the workflows, API server, and the counts server, it is useful to have a mock database available. 

During testing, a Docker container with official PostgresQL base image is brought up with Docker Compose. The image is imbued at build time with the "ADI" schema. The test data is then imported using the data import workflow. At this point the database is ready to support tests.

## `spt` tab completion

Bash completion has been implemented that allows the user the readily assess and find functionality provided at the command line. This reduces the need for some kinds of documentation, since it is folded in to the executables in such a way that it can be readily accessed.

After installation of the Python package, an entry point `spt` is created. (Use `spt-enable-completion` to manually install the completion to a shell profile file).

`spt [TAB]` yields the submodules which can be typed next.

`spt <module name> [TAB]` yields the commands provided by the given module.

`spt <module name> <command name> [TAB]` yields the `--help` text for the command.

For example:

```
$ spt [TAB]
countsserver  db  workflow

$ spt db [TAB]
create-schema  guess-channels-from-object-files  modify-constraints  status

$ spt db status [TAB]
usage: spt db create-schema [-h] [--database-config-file DATABASE_CONFIG_FILE] [--force] [--refresh-views-only | --recreate-views-only]

Create scstudies database with defined schema.

optional arguments:
  -h, --help            show this help message and exit
  --database-config-file DATABASE_CONFIG_FILE
                        Provide the file for database configuration.
  --force               By default, tables are created only if they don't already exist. If "force" is set, all tables from the schema are dropped
                        first. Obviously, use with care; all data in existing tables will be deleted.
  --refresh-views-only  Only refresh materialized views, do not touch main table schema.
  --recreate-views-only
                        Only recreate views, do not touch main table schema.
<press enter>
```

The current list of commands:

```sh
spt countsserver cache-expressions-data-array
spt countsserver start
spt db create-schema
spt db guess-channels-from-object-files
spt db modify-constraints
spt db status
spt workflow aggregate-core-results
spt workflow configure
spt workflow core-job
spt workflow extract-compartments
spt workflow generate-run-information
spt workflow initialize
spt workflow merge-performance-reports
spt workflow merge-sqlite-dbs
spt workflow report-on-logs
spt workflow report-run-configuratio
```

## `pyproject.toml` and package configuration improvements

Python packaging methods using a `setup.py` are being phased out infavor of a declarative configuration `pyproject.toml`. This is good for reproducible builds (library developers no longer write executable build steps, these being the responsibility of the build system like `pip`), as well as providing a parseable configuration for the library itself (e.g. to read off the version by parsing the TOML file).

We also make use of installation extras (external library dependencies grouped according to named flags explicit set at install time) to reduce virtual environment and container image sizes in case only submodules are needed.

## Installation hints

In some cases an installation extra is needed for a given command. For example, `spt db status --help` requires extra `[db]`:

```
spt db status ...
```

<pre>
<span style="color:olive;">
Got a module not found error.
Did you install the required extras with:</span><span style="color:green;">
    pip install &quot;spatialprofilingtoolbox[db]&quot;
</span><span style="color:olive;">?
</span>
</pre>

## Overall directory restructuring

This PR is the first time that the 4 indicated submodules have dedicated, separate directories. Many files needed to be moved, and imports needed to be restructured. For example, the database-related functions were previously spread out in the workflows area, especially the data import workflow, as well as in a supposedly common/basic utilities area. This is now corrected.

An attempt was also made to make the top level, seen on the GitHub landing page for the repository, as clean as possible.

## `adisinglecell`

The actual data model to support the single cell studies database is now placed in a completely [separate package](https://pypi.org/project/adisinglecell/), outside this repository.

## Development

A typical run currently looks like this:

```
$ make build-docker-images
```

<pre>
Creating virtual environment [building] <span style="color:olive;">...</span><span style="color:olive;">.....................................</span> <span style="font-weight:bold;color:green;">Created.</span>       <span style="color:purple;">(8s)</span>      
Creating spt CLI completions script <span style="color:olive;">...</span><span style="color:olive;">.........................................</span> <span style="font-weight:bold;color:green;">Created.</span>       <span style="color:purple;">(1s)</span>      
Building spatialprofilingtoolbox wheel using build==0.8.0 <span style="color:olive;">...</span><span style="color:olive;">...................</span> <span style="font-weight:bold;color:green;">Built.</span>         <span style="color:purple;">(13s)</span>     
Checking that Docker daemon is running <span style="color:olive;">...</span><span style="color:olive;">......................................</span> <span style="font-weight:bold;color:green;">Running.</span>       <span style="color:purple;">(0s)</span>      
Building Docker image nadeemlab/spt-apiserver <span style="color:olive;">...</span><span style="color:olive;">...............................</span> <span style="font-weight:bold;color:green;">Built.</span>         <span style="color:purple;">(6s)</span>      
Building Docker image nadeemlab/spt-countsserver <span style="color:olive;">...</span><span style="color:olive;">............................</span> <span style="font-weight:bold;color:green;">Built.</span>         <span style="color:purple;">(3s)</span>      
Building Docker image nadeemlab/spt-db <span style="color:olive;">...</span><span style="color:olive;">......................................</span> <span style="font-weight:bold;color:green;">Built.</span>         <span style="color:purple;">(10s)</span>     
Building Docker image nadeemlab/spt-workflow <span style="color:olive;">...</span><span style="color:olive;">................................</span> <span style="font-weight:bold;color:green;">Built.</span>         <span style="color:purple;">(20s)</span>     
</pre>

```
$ make test
```

<pre>
Creating virtual environment [apiserver] <span style="color:olive;">...</span><span style="color:olive;">....................................</span> <span style="font-weight:bold;color:green;">Created.</span>       <span style="color:purple;">(6s)</span>      
Creating virtual environment [db] <span style="color:olive;">...</span><span style="color:olive;">...........................................</span> <span style="font-weight:bold;color:green;">Created.</span>       <span style="color:purple;">(11s)</span>     
Creating virtual environment [workflow] <span style="color:olive;">...</span><span style="color:olive;">.....................................</span> <span style="font-weight:bold;color:green;">Created.</span>       <span style="color:purple;">(17s)</span>     
Creating virtual environment [all] <span style="color:olive;">...</span><span style="color:olive;">..........................................</span> <span style="font-weight:bold;color:green;">Created.</span>       <span style="color:purple;">(18s)</span>     
Testing API internal basic database accessor <span style="color:olive;">...</span><span style="color:olive;">................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(1s)</span>      
Testing binary expression viewer <span style="color:olive;">...</span><span style="color:olive;">............................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(0s)</span>      
Testing guess channels from object files <span style="color:olive;">...</span><span style="color:olive;">....................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(8s)</span>      
Testing signature cell set subsetting <span style="color:olive;">...</span><span style="color:olive;">.......................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(8s)</span>      
Testing single API route <span style="color:olive;">...</span><span style="color:olive;">....................................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(0s)</span>      
Testing single signature count query <span style="color:olive;">...</span><span style="color:olive;">........................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(0s)</span>      
Testing basic health of database <span style="color:olive;">...</span><span style="color:olive;">............................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(1s)</span>      
Testing drop recreate database constraints <span style="color:olive;">...</span><span style="color:olive;">..................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(2s)</span>      
Testing HALO exported data import <span style="color:olive;">...</span><span style="color:olive;">...........................................</span> <span style="font-weight:bold;color:green;">Passed.</span>        <span style="color:purple;">(15s)</span>     
</pre>

## Development machine requirements

- Postgres daemon disabled (or not installed)
- No other web server running on the machine (port 8080)
- Nextflow
- Java
- python3
- GNU Make
- PyPI credentials available (if doing source code releases)
- Docker Hub credentials available (if doing Docker Hub repository pushes)

## Still unfinished

Refactoring tasks (i.e. with functionality largely unchanged):

- Primary (README) documentation revision.
- Update maintainers/development documentation.
- Migration of many prior `tests/` into the test running pattern.
- Much refactoring to enable (fast) unit tests rather than only the more integration-style module tests.
- Add unit tests. (Some notes for possible tests are added to `unit_tests/`.)
- Unpin Python package dependencies, i.e. by providing a version number range rather than a single version. This requires at the minimum doing the test suite over a few different versions for these dependencies, at least once.

Other tasks:

- Migrate workflows to fully database-dependent versions, with almost no dependence on source files (except for the data import workflow).
- Include basic stats tests in export to database.















