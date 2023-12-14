The intended procedure for using `spt cggnn` (**c**ell **g**raph - **g**raph **n**eural **n**etwork) is:

1. [Explore the data available for a study and train the model](#explore-the-data-available-for-a-study-and-train-the-model)
2. [Configure a reproducible cggnn workflow](#configure-a-reproducible-cggnn-workflow)
3. [Running the workflow](#running-the-workflow)

# Explore the data available for a study and train the model

- Evaluate the specimen cohorts at your disposal with `spt cggnn explore-classes`.
- Select sample strata to use and fetch the relevant data artifacts from the database using `spt cggnn extract`.
- Use `spt cggnn train` to train and fine-tune your CG-GNN model.

# Configure a reproducible cggnn workflow

Use `spt workflow configure`, with the parameters obtained as above, to create artifacts that will reproducibly run through the entire process of gathering the data, training, and reporting with your trained model. Then your workflow can be run in one line using Nextflow to approximately reproduce your model and results.

Note that because the GNN uses non-deterministic algorithms, workflows will not be exactly reproducible.

You must provide the following parameters:

```
spt workflow configure --local --workflow='cggnn' --study-name=... --database-config-file=... --workflow-config-file=...
```

For canonical explanations of each parameter, please refer to the docstrings of the scripts being called by `spt workflow configure`, as shown by [the Nextflow file used for cggnn](spatialprofilingtoolbox/workflow/assets/cggnn.nf). The definitions are provided for quick reference only and may not be up to date.

`study-name` is the name of your study as it appears in your scstudies database instance, and `database-config-file` is the location of your database configuration file, in the format of [`.spt_db.config.template`](https://github.com/nadeemlab/SPT/blob/main/spatialprofilingtoolbox/workflow/assets/.spt_db.config.template).

`workflow-config-file` is more involved. Unused by other workflows (so far), it should be a YAML file following this template, as in [`.workflow.config.template`](https://github.com/nadeemlab/SPT/blob/main/spatialprofilingtoolbox/workflow/assets/.workflow.config.template):

```yaml
[settings]
strata = ...
validation_data_percent = ...
test_data_percent = ...
disable_channels = ...
disable_phenotypes = ...
cells_per_roi_target = ...
target_name = ...
in_ram = ...
batch_size = ...
epochs = ...
learning_rate = ...
k_folds = ...
explainer_model = ...
merge_rois = ...
upload_importances = ...
cuda = ...
random_seed = ...
```

Note that with this configuration file, parameters can't be eliminated to use the default value as is possible with CLI arguments.

* `strata`: Specimen strata to use as labels, identified according to the "stratum identifier" in `explore-classes`. This should be given as space separated integers. Can be set to `all` to use all strata.
* `validation_data_percent`: Percentage of data to use as validation data. Set to 0 if you want to do k-fold cross-validation. (Training percentage is implicit.)
* `test_data_percent`: Percentage of data to use as the test set. (Training percentage is implicit.)
* `disable_channels`: If true, disable the use of individual channel information in the graph. (Only named phenotypes, a.k.a. ``composite phenotypes", would appear.)
* `disable_phenotypes`: If true, disable the use of phenotype information in the graph. (Only individual channels would appear.)
* `cells_per_roi_target`: Target number of cells per region of interest (ROI). Used with the median cell density across all slides to choose what (one) ROI size will be chosen for the study. (The actual number of cells per ROI will vary as cell density isn't uniform across slides.)
* `target_name`: The name of a column in the dataframe whose true values indicate cells to be used when building ROIs. Can be set to `none` to use all cells in the sample.
* `in_ram`: If true, store the data in RAM.
* `batch_size`: Batch size to use during training.
* `epochs`: Number of training epochs to do.
* `learning_rate`: Learning rate to use during training.
* `k_folds`: Number of folds to use in cross validation. 0 means don't use k-fold cross validation unless no validation dataset is provided, in which case k defaults to 3.
* `explainer_model`: The explainer type to use. If not `none`, importance scores will be calculated using the model archetype chosen. `pp` is recommended.
* `merge_rois`: If true, return a CSV of importance scores merged together by sample.
* `upload_importances`: If true, importance scores will be uploaded to the database.
* `cuda`: If true, use CUDA to accelerate training.
* `random_seed`: An integer random seed to use for reproducibility. Can be set to `none` to omit a random seed.

# Running the workflow

The workflow spins up a Docker container with the necessary dependencies to run the workflow, so we recommend installing it before trying to run it. This workflow is accelerated if you have a CUDA-compatible GPU, and we recommend using a machine with CUDA support if at all possible. Once your configuration is ready, run the workflow with:

```sh
nextflow run .
```
