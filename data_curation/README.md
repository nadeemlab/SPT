The scripts in this directory are used to organize datasets before importing into a PostgreSQL database for the SPT application or analysis.

1. [Doing import / upload](#doing-import--upload)
2. [Doing import / upload for just one dataset](#doing-import--upload-for-just-one-dataset)
3. [Import without using the wrapper scripts](#import-without-using-the-wrapper-scripts)
4. [Show all progress](#show-progress)

Datasets are stored in subdirectories of `datasets/`. The procedure for adding a new dataset is documented in [`datasets/template/README.md`](datasets/template/README.md).

## Doing import / upload
A script which does a mass import of all available datasets is provided here as `import_datasets.sh`. It assumes that the [`spatialprofilingtoolbox` Python package](https://pypi.org/project/spatialprofilingtoolbox/) has been installed.

The usage is, for example:
```bash
./import_datasets.sh ~/.spt_db.config.local --drop-first
```
- `~/.spt_db.config.local` is an example name of a [database configuration file](https://github.com/nadeemlab/SPT/blob/main/spatialprofilingtoolbox/workflow/assets/.spt_db.config.template).
- The `--drop-first` option causes dropping/deleting a dataset with the same study name as one which is about to be uploaded. Without this option, upload will only take place if the dataset is not already in the database.

## Doing import / upload for just one dataset
For example:

```bash
./import_datasets.sh ~/.spt_db.config.local --drop-first moldoveanu
```
or
```bash
./import_datasets.sh ~/.spt_db.config.local --no-drop-first moldoveanu
```

## Import without using the wrapper
The import-all-datasets-here script is provided for convenience only, as a wrapper around `spt` CLI commands.

For one dataset you may prefer to use your own custom script templated on the following:

```bash
mkdir rundir; cd rundir
spt workflow configure --workflow="tabular import" --config-file=workflow.config
./run.sh
```

For the above, the `workflow.config` file should look something like this:
```ini
[general]
db_config_file = /Users/username/.spt_db.config.local

[database visitor]
study_name = Melanoma CyTOF ICI

[tabular import]
input_path = datasets/moldoveanu/generated_artifacts
```

If you wish for Nextflow to pull directly from S3, rather than a local directory like `.../generated_artifacts`, `workflow.config` may look like this instead:

```ini
[general]
db_config_file = /Users/username/.spt_db.config.local

[database visitor]
study_name = Melanoma CyTOF ICI

[tabular import]
input_path = s3://bucketname/moldoveanu
```

In the S3 case, you would have to make sure that credentials are available. Currently Nextflow requires, in the case of session-specific credentials, a "profile" in `~/.aws/credentials`, usually the profile named `default`.

You can monitor progress by watching the Nextflow logs:

```bash
tail -f -n1000 work/*/*.command.log
```

## Show all progress
By default `import_datasets.sh` is parallelized at the per-dataset level. To see basic progress across , use `./show_progress.sh` .
