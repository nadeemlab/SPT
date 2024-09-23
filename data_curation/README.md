The scripts here are used to import dataset into a PostgreSQL database for the SPT application or analysis, as well as organize or curate these datasets into a form acceptable for import.

1. [Curation or pre-processing](#curation-or-pre-processing)
2. [Doing import / upload into the database](#doing-import--upload-into-the-database)
3. [Finer control of upload process](#finer-control-of-upload-process)

# 1. Curation or pre-processing

Datasets are stored in subdirectories of `datasets/`. To prepare a new dataset, follow the full example [here](`datasets/moldoveanu/README.md`). The example includes files pre-generated in a format ready for import into the database, but you can also re-generate them yourself.

Extraction scripts tend to be dataset-specific, but there are some common tasks like quantification over segments in images, and formulation of standardized representations of channel or clinical metadata.


# 2. Doing import / upload into the database
Make sure that
- [`spatialprofilingtoolbox` Python package](https://pypi.org/project/spatialprofilingtoolbox/) has been installed, and
- PostgresQL is installed and running on your machine.

```sh
./import_datasets.sh ~/.spt_db.config.local --drop-first moldoveanu
```

- `~/.spt_db.config.local` is an example name of a [database configuration file](https://github.com/nadeemlab/SPT/blob/main/spatialprofilingtoolbox/workflow/assets/.spt_db.config.template).
- The `--drop-first` option causes dropping/deleting a dataset with the same study name as one which is about to be uploaded. Without this option, upload will only take place if the dataset is not already in the database.
- `moldoveanu` is the name of the dataset subdirectory for the complete example.


# 3. Finer control of the upload process
The usage above uses several convenience wrapper functions, and assumes that you have saved dataset artifacts to `datasetes/<dataset_name>/generated_artifacts/`.

For finer control, for example when drawing source files from an S3 bucket, use the following:

```bash
mkdir rundir; cd rundir
spt workflow configure --workflow="tabular import" --config-file=workflow.config
./run.sh
```

Here the `workflow.config` file should look something like this:
```ini
[general]
db_config_file = /Users/username/.spt_db.config.local

[database visitor]
study_name = Melanoma CyTOF ICI

[tabular import]
input_path = datasets/moldoveanu/generated_artifacts
```

If you wish for Nextflow (which runs in `run.sh`) to pull source files directly from S3, `workflow.config` may look like this instead:

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
