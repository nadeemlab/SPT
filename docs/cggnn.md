The intended procedure for using `spt cggnn` (**c**ell **g**raph - **g**raph **n**eural **n**etwork) is:

1. [Explore the data available for a study and train the model](#explore-the-data-available-for-a-study-and-train-the-model)
2. [Configure a reproducible cggnn workflow](#configure-a-reproducible-cggnn-workflow)
3. [Running the workflow](#running-the-workflow)

# Explore the data available for a study and train the model

i. Evaluate the specimen cohorts at your disposal with `spt cggnn explore-classes`.
ii. Select sample strata to use and fetch the relevant data artifacts from the database using `spt cggnn extract`.
iii. Use `spt cggnn run` or the `cg-gnn` pip package directly to train and fine-tune your CG-GNN model.

# Configure a reproducible cggnn workflow

Use `spt workflow configure`, with the parameters obtained as above, to create artifacts that will reproducibly run through the entire process of gathering the data, training, and reporting with your trained model. Then your workflow can be run in one line using Nextflow to approximately reproduce your model and results.

Note that because the GNN uses non-deterministic algorithms, workflows will not be exactly reproducible.

You must provide the following parameters:

```
spt workflow configure --local --workflow='cggnn' --study-name=... --database-config-file=... --workflow-config-file=...
```

For canonical explanations of each parameter, please refer to the docstrings of the scripts being called by `spt workflow configure`, as shown by [the Nextflow file used for cggnn](spatialprofilingtoolbox/workflow/assets/cggnn.nf), and the [`cg-gnn` pip package](https://pypi.org/project/cg-gnn/) documentation. The definitions are provided for quick reference only and may not be up to date.

`study-name` is the name of your study as it appears in your scstudies database instance, and `database-config-file` is the location of your database configuration file, in the format of [`.spt_db.config.template`](https://github.com/nadeemlab/SPT/blob/main/spatialprofilingtoolbox/workflow/assets/.spt_db.config.template).

`workflow-config-file` is more involved. Unused by other workflows (so far), it should be a YAML file following this template, as in [`.workflow.config.template`](https://github.com/nadeemlab/SPT/blob/main/spatialprofilingtoolbox/workflow/assets/.workflow.config.template):

```yaml
[settings]
strata = ...
validation_data_percent = ...
test_data_percent = ...
disable_channels = ...
disable_phenotypes = ...
cells_per_slide_target = ...
target_name = ...
in_ram = ...
batch_size = ...
epochs = ...
learning_rate = ...
k_folds = ...
explainer_model = ...
merge_rois = ...
upload_importances = ...
```

Note that with this configuration file, parameters can't be eliminated to use the default value as is possible with CLI arguments.

* `strata`: Specimen strata to use as labels, identified according to the "stratum identifier" in `explore-classes`. This should be given as space separated integers. Can be set to `all` to use all strata.
* `validation_data_percent`: Percentage of data to use as validation data. Set to 0 if you want to do k-fold cross-validation. (Training percentage is implicit.)
* `test_data_percent`: Percentage of data to use as the test set. (Training percentage is implicit.)
* `disable_channels`: If true, disable the use of individual channel information in the graph. (Only named phenotypes, a.k.a. ``composite phenotypes", would appear.)
* `disable_phenotypes`: If true, disable the use of phenotype information in the graph. (Only individual channels would appear.)
* `cells_per_slide_target`: An intended target number of cells per slide, used with the median cell density across all slides during determination of the ROI size.
* `target_name`: The name of a column in the dataframe whose true values indicate cells to be used when building ROIs. Can be set to `none` to use all cells in the sample.
* `in_ram`: If true, store the data in RAM.
* `batch_size`: Batch size to use during training.
* `epochs`: Number of training epochs to do.
* `learning_rate`: Learning rate to use during training.
* `k_folds`: Number of folds to use in cross validation. 0 means don't use k-fold cross validation unless no validation dataset is provided, in which case k defaults to 3.
* `explainer_model`: The explainer type to use. If not `none`, importance scores will be calculated using the model archetype chosen. `pp` is recommended.
* `merge_rois`: If true, return a CSV of importance scores merged together by sample.
* `upload_importances`: If true, importance scores will be uploaded to the database.
* `random_seed`: An integer random seed to use for reproducibility. Can be set to `none` to omit a random seed.

# Running the workflow

The conda environment file [`cggnn_environment.yml`](cggnn_environment.yml) specifies the installation of the minimum dependencies required to run the workflow fluidly. The environment assumes the machine you are running the workflow on has a CUDA-compatible GPU. Running the cggnn workflow without CUDA is not recommended, but if you choose to do so use [`cggnn_environment_no_cuda.yml`](cggnn_environment_no_cuda.yml). If your machine does support CUDA but not CUDA 11.8, you will need to change the version used by CUDA, pytorch, and DGL to a version your GPU supports.

Assuming you have conda installed [(instructions here)](https://conda.io/projects/conda/en/latest/user-guide/install/index.html), create the environment and activate it with the following commands:

```sh
conda env create -f docs/cggnn_environment.yml
conda activate spt_cggnn
```

Then run with:
```sh
nextflow run .
```
