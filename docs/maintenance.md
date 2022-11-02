# Development, maintenance, administration

The modules in this repository are built, tested, and deployed using `make` and Docker.

| Development environment software requirements              | Version required or tested under |
| ---------------------------------------------------------- | -------------------------------  |
| Unix-like operating system                                 | Darwin 20.6.0 and Ubuntu 20.04   |
| [GNU Make](https://www.gnu.org/software/make/)             | 4.2.1                            |
| [Docker Engine](https://docs.docker.com/engine/install/)   | 20.10.17                         |
| [Docker Compose](https://docs.docker.com/compose/install/) | 2.10.2                           |
| [bash](https://www.gnu.org/software/bash/)                 | >= 4                             |
| [python](https://www.python.org/downloads/)                | >=3.7                            |

A typical development workflow looks like:

1. Modify or add source files.
2. Add new unit and "module" tests.
3. `$ make clean`
<pre>
Checking that Docker daemon is running <span style="color:olive;">...</span><span style="color:olive;">......................................</span> <span style="font-weight:bold;color:green;">Running.</span>       <span style="color:purple;">(1s)</span>
Running docker compose rm (remove) <span style="color:olive;">...</span><span style="color:olive;">..........................................</span> <span style="font-weight:bold;color:green;">Down.</span>          <span style="color:purple;">(1s)</span>
</pre>
4. `$ make test`


```txt
Creating venv for basic package introspection .................................. Created.       (4s)      
Creating spt CLI completions script ............................................ Created.       (5s)      
Building development image ..................................................... Built.         (14s)     
Building apiserver Dockerfile .................................................. Built.         (0s)      
Building countsserver Dockerfile ............................................... Built.         (0s)      
Building db Dockerfile ......................................................... Built.         (0s)      
Building workflow Dockerfile ................................................... Built.         (0s)      
Building Docker image nadeemlab/spt-db ......................................... Built.         (10s)     
Building test-data-loaded spt-db image (1) ..................................... Built.         (19s)     
Building test-data-loaded spt-db image (1and2) ................................. Built.         (36s)     
Building Docker image nadeemlab/spt-apiserver .................................. Built.         (10s)     
Building Docker image nadeemlab/spt-countsserver ............................... Built.         (10s)     
Building Docker image nadeemlab/spt-workflow ................................... Built.         (10s)     
Running docker compose rm (remove) ............................................. Down.          (0s)      
apiserver (setup testing environment) .......................................... Setup.         (3s)      
  API internal basic database accessor ......................................... Passed.        (1s)      
apiserver (teardown testing environment) ....................................... Down.          (1s)      
countsserver (setup testing environment) ....................................... Setup.         (1s)      
  binary expression viewer ..................................................... Passed.        (1s)      
countsserver (teardown testing environment) .................................... Down.          (0s)      
db (setup testing environment) ................................................. Setup.         (2s)      
  drop recreate database constraints ........................................... Passed.        (3s)      
  guess channels from object files ............................................. Passed.        (1s)      
db (teardown testing environment) .............................................. Down.          (0s)      
workflow (setup testing environment) ........................................... Setup.         (3s)      
  signature cell set subsetting ................................................ Passed.        (1s)      
workflow (teardown testing environment) ........................................ Down.          (0s)      
apiserver (setup testing environment) .......................................... Setup.         (3s)      
  single API route ............................................................. Passed.        (0s)      
  counts query delegation edge cases ........................................... Passed.        (1s)      
apiserver (teardown testing environment) ....................................... Down.          (1s)      
countsserver (setup testing environment) ....................................... Setup.         (1s)      
  class counts cohoused datasets ............................................... Passed.        (1s)      
  expression data caching ...................................................... Passed.        (2s)      
  edge cases few markers ....................................................... Passed.        (1s)      
  single signature count query ................................................. Passed.        (0s)      
countsserver (teardown testing environment) .................................... Down.          (1s)      
db (setup testing environment) ................................................. Setup.         (3s)      
  basic health of database ..................................................... Passed.        (1s)      
  record counts cohoused datasets .............................................. Passed.        (1s)      
db (teardown testing environment) .............................................. Down.          (0s)      
workflow (setup testing environment) ........................................... Setup.         (2s)      
  proximity pipeline ........................................................... Passed.        (71s)     
workflow (teardown testing environment) ........................................ Down.          (1s)
```

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
Uploading spatialprofilingtoolbox==0.11.0 to PyPI <span style="color:olive;">...</span><span style="color:olive;">...........................</span> <span style="font-weight:bold;color:green;">Uploaded.</span>      <span style="color:purple;">(3s)</span>
</pre>

### Python package
The source code is contained in one Python package, `spatialprofilingtoolbox`. The package metadata uses the declarative `pyproject.toml` format.

### Modules
The main functionality is provided by 4 modules designed to operate as services. Each module's source is wrapped in a Docker image.

| Module name     | Description |
| --------------- | ----------- |
| `apiserver`     | FastAPI application supporting queries over cell data. |
| `countsserver`  | An optimized class-counting program served by a custom TCP server. |
| `db`            | Data model/interface and PostgresQL database management SQL fragments. |
| `workflow`      | [Nextflow](https://www.nextflow.io)-orchestrated computation workflows. |

- *The `db` module is for testing only. A real PostgresQL database should generally not be deployed in a container.*

### Test-managed development
Test scripts are located under
- `spatialprofilingtoolbox/<module name>/unit_tests`
- `spatialprofilingtoolbox/<module name>/module_tests`

These tests serve multiple purposes for us:
1. To verify preserved functionality during source code modification.
2. To exemplify typical usage of classes and functions, including how they are wrapped in a container and how that container is setup.

Each test is performed inside an isolated for-development-only `spatialprofilingtoolbox`-loaded Docker container, in the presence of a running module-specific Docker composition that provides the given module's service as well as other modules' services (if needed).

### `spt` tab completion
You might want to install `spatialprofilingtoolbox` to your local machine in order to initiate database control actions, ETL, etc.

In this case bash completion is available that allows you to readily assess and find functionality provided at the command line. This reduces the need for some kinds of documentation, since such documentation is already folded in to the executables in such a way that it can be readily accessed.

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
  --recreate-views-only Only recreate views, do not touch main table schema.
```



