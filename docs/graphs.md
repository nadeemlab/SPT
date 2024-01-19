# How to train graph transformation models using SPT

The intended procedure for using `spt graphs` and graph workflows is:

1. [Prerequisites](#install-prerequisites)
2. [Explore the data available for a study and train the model](#explore-the-data-available-for-a-study-and-train-the-model)
3. [Configure a reproducible graph transformation workflow](#configure-a-reproducible-graph-transformation-workflow)
4. [Run the workflow](#run-the-workflow)

## Install prerequisites

Our graph transformation workflows are powered by [Nextflow](https://www.nextflow.io/docs/latest/getstarted.html) and [Docker](https://docs.docker.com/engine/install/) or [Singularity](https://docs.sylabs.io/guides/3.0/user-guide/installation.html), in addition to the SPT Python package. Please ensure all three are installed before proceeding.
```sh
# Install Docker or Singularity per the links above
curl -s https://get.nextflow.io | bash
pip install spatialprofilingtoolbox[workflow]
```

## Explore the data available for a study and train the model

- Evaluate the specimen cohorts at your disposal with `spt graphs explore-classes`.
- Select sample strata to use and fetch graph data artifacts from the database using `spt graphs extract`.
- Use an [SPT plugin](https://github.com/nadeemlab/spt-plugin) to transform your graph data into results, including cell-level importance scores.

## Configure a (mostly) reproducible graph transformation workflow

To create artifacts that will reproducibly run through the entire process of gathering the data, transforming it, and reporting results in one line using Nextflow, we provide the `spt workflow configure` utility. It uses the parameters obtained from the last step to create this reproducible workflow.

Currently, we have one graph transformation workflow available in SPT, `cg-gnn`, which trains a cell graph neural network (CG-GNN) model and returns importance scores for cells used to train and test the model. We plan to add more workflows in the future. If you'd like to develop your own, please refer to the [spt-plugin repository](https://github.com/nadeemlab/spt-plugin) for more information.

(Note that because most deep learning models like CG-GNN uses non-deterministic algorithms, workflows will not be exactly reproducible.)

To configure graph transformation workflows like `cg-gnn`, use the following command:
```
spt workflow configure --workflow=<YOUR WORKFLOW> --config-file=<YOUR CONFIG FILE LOCATION>
```

### The workflow configuration file

For a template of the workflow configuration file, see [`.workflow.config.template`](spatialprofilingtoolbox/workflow/assets/.workflow.config.template). It's reproduced here with definitions for quick reference, but this doc may not be as up to date as the source code. For canonical explanations of each parameter, please refer to the docstrings of the scripts being called by `spt workflow configure`, as shown by [the Nextflow file used for cggnn](spatialprofilingtoolbox/workflow/assets/cggnn.nf).

```ini
[general]
db_config_file = path/to/db.config
container_platform = None
image_tag = latest

[database visitor]
study_name = name_of_study

[cg-gnn]
graph_config_file = path/to/graph.config
cuda = true
upload_importances = false
```

General
* `database-config-file` is the location of your database configuration file, in the format of [`.spt_db.config.template`](https://github.com/nadeemlab/SPT/blob/main/spatialprofilingtoolbox/workflow/assets/.spt_db.config.template).
* `container-platform` is the container platform to use. Can be `None`, `docker`, or `singularity`. If `None`, no container platform will be used, but a container platform is required to run graph transformation workflows.
* `image-tag` is the tag of the container image associated with each workflow to use. If `None`, the latest image will be used.

Database visitor. These parameters apply to any workflow that queries the database.
* `study-name` is the name of your study as it appears in your scstudies database instance

CG-GNN. These parameters are specific to the CG-GNN workflow. If you define your own workflow or plugin, we recommend creating a new section but using a similar format.
* `graph_config_file` is the location of your graph configuration file, in [`this format`](spatialprofilingtoolbox/graphs/template.config). See below for more information.
* `cuda` is whether to use CUDA to accelerate training. If `false`, the CPU will be used instead.
* `upload_importances` is whether to upload importance scores calculated by your graph transformation workflow to the database.

### The graph configuration file

[The template from the graphs submodule](spatialprofilingtoolbox/graphs/template.config) is reproduced here for quick reference, but again please refer to the source code for the most up to date information. The values supplied here generally correspond to the default arguments (`db_config_file_path`, `study_name`, and `strata` excepted) so you can omit them if you want to use the defaults.

```ini
[general]
db_config_file_path = path/to/db.config
study_name = Study name in SPT database
random_seed = None

[extract]
strata = 1 2 3

[graph-generation]
validation_data_percent = 20
test_data_percent = 20
use_channels = true
use_phenotypes = true
roi_side_length = None
cells_per_roi_target = 10000
max_cells_to_consider = 100000
target_name = None
exclude_unlabeled = false
n_neighbors = 5
threshold = None

[upload-importances]
cohort_stratifier = None
```

Note that with this configuration file, parameters can't be eliminated to use the default value as is possible with CLI arguments.

General
* `db_config_file_path`: same as `database-config-file` in the workflow configuration file
* `study_name`: same as `study-name` in the workflow configuration file
* `random_seed`: Whether to use a random seed for reproducibility. If `None`, no random seed will be used.

Extract
* `strata`: Specimen strata to use as labels, identified according to the "stratum identifier" in `explore-classes`. This should be given as space separated integers. Can be set to `all` to use all strata.

Graph generation
* `validation_data_percent`: Percentage of data to use as validation data. Set to 0 if you want to do k-fold cross-validation. (Training percentage is implicit.)
* `test_data_percent`: Percentage of data to use as the test set. (Training percentage is implicit.)
* `use_channels`: If false, disable the use of individual channel information in the graph. (Only named phenotypes, a.k.a. ``composite phenotypes", would appear.)
* `use_phenotypes`: If false, disable the use of phenotype information in the graph. (Only individual channels would appear.)
* `roi_side_length`: Side length of the square region of interest (ROI) to use. If `None`, `cells_per_roi_target` overrules.
* `cells_per_roi_target`: Target number of cells per region of interest (ROI). Used with the median cell density across all slides to choose what (one) ROI size will be chosen for the study. (The actual number of cells per ROI will vary as cell density isn't uniform across slides.)
* `max_cells_to_consider`: Maximum number of cells to consider when building ROIs. If `None`, all cells will be considered.
* `target_name`: The name of a column in the dataframe whose true values indicate cells to be used when building ROIs. Can be set to `none` to use all cells in the sample.
* `exclude_unlabeled`: If true, exclude specimens with no label from graph generation.
* `n_neighbors`: Number of nearest neighboring cells to use when building the cell graph.
* `threshold`: Distance threshold to use when considering if two cells are neighbors. If `None`, no threshold will be used.

CG-GNN
* `in_ram`: If true, store the data in RAM.
* `batch_size`: Batch size to use during training.
* `epochs`: Number of training epochs to do.
* `learning_rate`: Learning rate to use during training.
* `k_folds`: Number of folds to use in cross validation. 0 means don't use k-fold cross validation unless no validation dataset is provided, in which case k defaults to 3.
* `explainer_model`: The explainer type to use. If not `none`, importance scores will be calculated using the model archetype chosen. `pp` is recommended.
* `merge_rois`: If true, return a CSV of importance scores merged together by sample.

Upload importances
* `upload_importances`: If true, importance scores will be uploaded to the database.

# Run the workflow

The workflow spins up a Docker container with the necessary dependencies to run the workflow, so we recommend installing it before trying to run it. Once `spt workflow configure` finishes setting up, run the workflow with:

```sh
nextflow run .
```

If you're using Singularity, note that the Docker image to Singularity image conversion process can consume a lot of disk space. If you run into space issues, consider setting the [`SINGULARITY_TMPDIR`](https://docs.sylabs.io/guides/3.5/user-guide/appendix.html) environment variable to a directory on a drive with more space before running nextflow. We observed on our HPC that by default temporary files were stored in a `/tmp/` directory in a 12GB partition, which was insufficient for converting the Docker image. You can also set [`NXF_SINGULARITY_CACHEDIR`](https://github.com/nextflow-io/nextflow/issues/2685) to a directory with more space to store the converted Singularity images.
