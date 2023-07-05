# Development, maintenance, administration

1. <a href="#building-and-testing-modules">Building and testing modules</a>
2. <a href="#python-package">Python package</a>
3. <a href="#modules">Modules</a>
4. <a href="#test-managed-development">Test-managed development</a>
5. <a href="#spt-tab-completion">`spt` tab-completion</a>
6. <a href="#throwaway-testing">Throwaway testing</a>
7. <a href="#new-workflows">Add a new workflow</a>

## <a id="building-and-testing-modules"></a> 1. Building and testing modules

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
2. Add new tests.
3. `$ make clean`
<pre>
Checking that Docker daemon is running <span style="color:olive;">...</span><span style="color:olive;">......................................</span> <span style="font-weight:bold;color:green;">Running.</span>       <span style="color:purple;">(1s)</span>
Running docker compose rm (remove) <span style="color:olive;">...</span><span style="color:olive;">..........................................</span> <span style="font-weight:bold;color:green;">Down.</span>          <span style="color:purple;">(1s)</span>
</pre>
4. `$ make test`

```txt
Creating pyproject.toml ........................................................ Created.       (0s)
Building development image precursor ........................................... Built.         (0s)
Building development image ..................................................... Built.         (1s)
Building apiserver Dockerfile .................................................. Built.         (0s)
Building cggnn Dockerfile ...................................................... Built.         (0s)
Building ondemand Dockerfile ................................................... Built.         (0s)
Building db Dockerfile ......................................................... Built.         (0s)
Building workflow Dockerfile ................................................... Built.         (0s)
Checking for Docker credentials in ~/.docker/config.json ....................... Found.         (0s)
Building Docker image nadeemlab/spt-db ......................................... Built.         (6s)
Building test-data-loaded spt-db image (1small) ................................ Built.         (0s)
Building test-data-loaded spt-db image (1) ..................................... Built.         (0s)
Building test-data-loaded spt-db image (1and2) ................................. Built.         (1s)
Building Docker image nadeemlab/spt-apiserver .................................. Built.         (5s)
Building Docker image nadeemlab/spt-cggnn ...................................... Built.         (6s)
Building Docker image nadeemlab/spt-ondemand ................................... Built.         (6s)
Building Docker image nadeemlab/spt-workflow ................................... Built.         (6s)
Running docker compose rm (remove) ............................................. Down.          (1s)
apiserver (setup testing environment) .......................................... Setup.         (4s)
  study names .................................................................. Passed.        (1s)
  record counts ................................................................ Passed.        (4s)
  API internal basic database accessor ......................................... Passed.        (1s)
  expressions in db ............................................................ Passed.        (1s)
apiserver (teardown testing environment) ....................................... Down.          (1s)
cggnn (setup testing environment) .............................................. Setup.         (2s)
  image runs properly .......................................................... Passed.        (1s)
cggnn (teardown testing environment) ........................................... Down.          (1s)
ondemand (setup testing environment) ........................................... Setup.         (4s)
  binary expression viewer ..................................................... Passed.        (1s)
  intensity values imported .................................................... Passed.        (4s)
ondemand (teardown testing environment) ........................................ Down.          (0s)
db (setup testing environment) ................................................. Setup.         (3s)
  guess channels from object files ............................................. Passed.        (1s)
  drop recreate database constraints ........................................... Passed.        (13s)
  shapefile polygon extraction ................................................. Passed.        (1s)
db (teardown testing environment) .............................................. Down.          (0s)
workflow (setup testing environment) ........................................... Setup.         (3s)
  centroid pulling ............................................................. Passed.        (3s)
  feature matrix extraction .................................................... Passed.        (26s)
  stratification pulling ....................................................... Passed.        (2s)
  signature cell set subsetting ................................................ Passed.        (1s)
  sample stratification ........................................................ Passed.        (1s)
workflow (teardown testing environment) ........................................ Down.          (1s)
Building test-data-loaded spt-db image (1smallnointensity) ..................... Built.         (0s)
apiserver (setup testing environment) .......................................... Setup.         (5s)
  phenotype criteria ........................................................... Passed.        (0s)
  proximity .................................................................... Passed.        (4s)
  phenotype summary ............................................................ Passed.        (0s)
  retrieval of umap plots ...................................................... Passed.        (5s)
  retrieval of hi res umap ..................................................... Passed.        (1s)
  study summary retrieval ...................................................... Passed.        (0s)
  counts query delegation edge cases ........................................... Passed.        (1s)
apiserver (teardown testing environment) ....................................... Down.          (1s)
cggnn (teardown testing environment) ........................................... Down.          (0s)
ondemand (setup testing environment) ........................................... Setup.         (4s)
  expression data caching ...................................................... Passed.        (13s)
  class counts cohoused datasets ............................................... Passed.        (1s)
  edge cases few markers ....................................................... Passed.        (1s)
  single signature count query ................................................. Passed.        (0s)
ondemand (teardown testing environment) ........................................ Down.          (1s)
db (setup testing environment) ................................................. Setup.         (3s)
  basic health of database ..................................................... Passed.        (5s)
  expression table indexing .................................................... Passed.        (13s)
  record counts cohoused datasets .............................................. Passed.        (4s)
  fractions assessment ......................................................... Passed.        (4s)
db (teardown testing environment) .............................................. Down.          (0s)
workflow (setup testing environment) ........................................... Setup.         (3s)
  proximity pipeline ........................................................... Passed.        (95s)
  umap plot creation ........................................................... Passed.        (56s)
workflow (teardown testing environment) ........................................ Down.          (1s)
```

Optionally, if the images are ready to be released:

- `$ make build-and-push-docker-images`

<pre>
Checking for Docker credentials in ~/.docker/config.json <span style="color:olive;">...</span><span style="color:olive;">....................</span> <span style="font-weight:bold;color:green;">Found.</span>         <span style="color:purple;">(0s)</span>
Pushing Docker container nadeemlab/spt-apiserver <span style="color:olive;">...</span><span style="color:olive;">............................</span> <span style="font-weight:bold;color:green;">Pushed.</span>        <span style="color:purple;">(16s)</span>
Pushing Docker container nadeemlab/spt-ondemand <span style="color:olive;">...</span><span style="color:olive;">.............................</span> <span style="font-weight:bold;color:green;">Pushed.</span>        <span style="color:purple;">(15s)</span>
Pushing Docker container nadeemlab/spt-db <span style="color:olive;">...</span><span style="color:olive;">...................................</span> <span style="font-weight:bold;color:green;">Pushed.</span>        <span style="color:purple;">(23s)</span>
Pushing Docker container nadeemlab/spt-workflow <span style="color:olive;">...</span><span style="color:olive;">.............................</span> <span style="font-weight:bold;color:green;">Pushed.</span>        <span style="color:purple;">(27s)</span>
</pre>

If the package source code is ready to be released to PyPI:

- `$ make release-package`

<pre>
Checking for PyPI credentials in ~/.pypirc for spatialprofilingtoolbox <span style="color:olive;">...</span><span style="color:olive;">......</span> <span style="font-weight:bold;color:green;">Found.</span>         <span style="color:purple;">(0s)</span>
Uploading spatialprofilingtoolbox==0.11.0 to PyPI <span style="color:olive;">...</span><span style="color:olive;">...........................</span> <span style="font-weight:bold;color:green;">Uploaded.</span>      <span style="color:purple;">(3s)</span>
</pre>

## <a id="python-package"></a> 2. Python package
The source code is contained in one Python package, `spatialprofilingtoolbox`. The package metadata uses the declarative `pyproject.toml` format.

## <a id="modules"></a> 3. Modules
The main functionality is provided by 4 modules designed to operate as services. Each module's source is wrapped in a Docker image.

| Module name     | Description |
| --------------- | ----------- |
| `apiserver`     | FastAPI application supporting queries over cell data. |
| `cggnn`         | Command line tool to apply cell graph neural network models to data stored in an SPT framework. |
| `ondemand`      | An optimized class-counting and other metrics-calculation program served by a custom TCP server. |
| `db`            | Data model/interface and PostgresQL database management SQL fragments. |
| `workflow`      | [Nextflow](https://www.nextflow.io)-orchestrated computation workflows. |

- *The `db` module is for testing only. A real PostgresQL database should generally not be deployed in a container.*

## <a id="test-managed-development"></a> 4. Test-managed development
Test scripts are located under `test/`.

These tests serve multiple purposes for us:
1. To verify preserved functionality during source code modification.
2. To exemplify typical usage of classes and functions, including how they are wrapped in a container and how that container is setup.

Each test is performed inside an isolated for-development-only `spatialprofilingtoolbox`-loaded Docker container, in the presence of a running module-specific Docker composition that provides the given module's service as well as other modules' services (if needed).

## <a id="spt-tab-completion"></a> 5. `spt` tab completion
You might want to install `spatialprofilingtoolbox` to your local machine in order to initiate database control actions, ETL, etc.

In this case bash completion is available that allows you to readily assess and find functionality provided at the command line. This reduces the need for some kinds of documentation, since such documentation is already folded in to the executables in such a way that it can be readily accessed.

After installation of the Python package, an entry point `spt` is created. (Use `spt-enable-completion` to manually install the completion to a shell profile file).
- `spt [TAB]` yields the submodules which can be typed next.
- `spt <module name> [TAB]` yields the commands provided by the given module.
- `spt <module name> <command name> [TAB]` yields the `--help` text for the command.

For example:

```
$ spt [TAB]
apiserver ondemand  db  workflow

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

## <a id="throwaway-testing"></a> 6. Throwaway testing

Development often entails "throwaway" test scripts that you modify and run frequently in order to check your understanding of functionality and verify that it works as expected.

For this purpose, a pattern that has worked for me in this repository is:

1. Ensure at least one successful run of `make build-docker-images` at the top level of this repository's directory, for each module that you will use.
2. Go into the build are for a pertinent module: `cd build/<module name>`.
3. Create `throwaway_script.py`.
4. Setup the testing environment:
```sh
docker compose up -d
```
5. As many times as you need to, run your script with the following (replacing `<module name>`):
```
test_cmd="cd /mount_sources/<module name>/; python throwaway_script.py" ;
docker run \
  --rm \
  --network <module name>_isolated_temporary_test \
  --mount type=bind,src=$(realpath ..),dst=/mount_sources \
  -t nadeemlab-development/spt-development:latest \
  /bin/bash -c "$test_cmd";
```
6. Tear down the testing environment when you're done:
```sh
docker compose down;
docker compose rm --force --stop;
```

You can of course also modify the testing environment, involving more or fewer modules, even docker containers from external images, by editing `compose.yaml`.

## <a id="new-workflows"></a> 7. Add a new workflow

The computation workflows are orchestrated with Nextflow, using the process definition script [`main_visitor.nf`](https://github.com/nadeemlab/SPT/blob/main/spatialprofilingtoolbox/workflow/assets/main_visitor.nf). "Visitor" refers to the visitor pattern, whereby the process steps access the database, do some reads, do some computations, and return some results by sending them to the database.

Each workflow consists of:
- "job" definition (in case the workflow calls for parallelization)
- initialization
- core jobs
- integration/wrap-up

**To make a new workflow**: copy the `phenotype_proximity` subdirectory to a sibling directory with a new name. Update the components accordingly, and update [`workflow/__init__.py`](https://github.com/nadeemlab/SPT/blob/main/spatialprofilingtoolbox/workflow/__init__.py) with a new entry for your workflow, to ensure that it is discovered. You'll also need to update [`pyproject.toml`](https://github.com/nadeemlab/SPT/blob/main/pyproject.toml.unversioned) to declare your new subpackage.
