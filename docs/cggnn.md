# Using `spt cggnn`

The intended procedure for using `spt cggnn` (**c**ell **g**raph - **g**raph **n**eural **n**etwork) is:
1. Explore the data available for the study of your choice and train the model.
   1. Evaluate the specimen cohorts at your disposal with `spt cggnn explore-classes`.
   2. Now that you know which specimen cohorts ("strata") you want to use, fetch the relevant data artifacts from SPT using `spt cggnn extract`.
   3. Artifacts in hand, use `spt cggnn run` or the `cg-gnn` pip package directly to train and fine-tune your CG-GNN model.
2. Given that you now know the parameters you used to arrive at your fine-tuned CG-GNN model, use `spt workflow configure` to create artifacts that will reproducibly run through the entire process of gathering the data for, training, and reporting with your trained model. Then, your workflow can be run in one line using Nextflow to approximately reproduce your model and results.

This document will go into more detail on the second step.

## Configuring the cggnn workflow with `spt workflow configure`

To configure the `cggnn` SPT workflow, you must provide the following parameters as follows:

```
spt workflow configure --local --workflow='cggnn' --study-name=... --database-config-file=... --workflow-config-file=...
```

`study-name` is the name of your study as known by your SPT database instance, and `database-config-file` is the location of your database configuration file, in the format of [`.spt_db.config.template`](https://github.com/nadeemlab/SPT/blob/main/spatialprofilingtoolbox/workflow/assets/.spt_db.config.template).

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
prune_misclassified = ...
output_prefix = ...
upload_importances = ...
```

For detailed explanations of each parameter, please refer to the docstring for `spt cggnn run` (shown below, for most up-to-date version run the command with `--help`), or the [`cg-gnn`](https://pypi.org/project/cg-gnn/) documentation for even finer detail.

```txt
usage: spt cggnn run [-h] --spt_db_config_location SPT_DB_CONFIG_LOCATION --study STUDY [--strata STRATA [STRATA ...]] [--validation_data_percent VALIDATION_DATA_PERCENT] [--test_data_percent TEST_DATA_PERCENT] [--disable_channels] [--disable_phenotypes] [--roi_side_length ROI_SIDE_LENGTH] [--cells_per_slide_target CELLS_PER_SLIDE_TARGET] [--target_name TARGET_NAME]
                     [--in_ram] [-b BATCH_SIZE] [--epochs EPOCHS] [-l LEARNING_RATE] [-k K_FOLDS] [--explainer_model EXPLAINER_MODEL] [--merge_rois] [--prune_misclassified] [--output_prefix OUTPUT_PREFIX] [--upload_importances] [--random_seed RANDOM_SEED]

Create cell graphs from SPT tables saved locally, train a graph neural network on them, and save resultant model, metrics, and visualizations (if requested) to file. `spt cggnn run` allows you to run the `cg-gnn` pip package directly from SPT. It combines `spt cggnn extract` with the entire `cggnn.run` process into a single command.

options:
  -h, --help            show this help message and exit
  --spt_db_config_location SPT_DB_CONFIG_LOCATION
                        File location for SPT DB config file.
  --study STUDY         Name of the study to query data for in SPT.
  --strata STRATA [STRATA ...]
                        Specimen strata to use as labels, identified according to the "stratum identifier" in `explore-classes`. This should be given as space separated integers. If not provided, all strata will be used.
  --validation_data_percent VALIDATION_DATA_PERCENT
                        Percentage of data to use as validation data. Set to 0 if you want to do k-fold cross-validation later. (Training percentage is implicit.) Default 15%.
  --test_data_percent TEST_DATA_PERCENT
                        Percentage of data to use as the test set. (Training percentage is implicit.) Default 15%.
  --disable_channels    Disable the use of channel information in the graph.
  --disable_phenotypes  Disable the use of phenotype information in the graph.
  --roi_side_length ROI_SIDE_LENGTH
                        Side length in pixels of the ROI areas we wish to generate.
  --cells_per_slide_target CELLS_PER_SLIDE_TARGET
                        Used with the median cell density across all slides to determine the ROI size.
  --target_name TARGET_NAME
                        If given, build ROIs based only on cells with true values in this DataFrame column.
  --in_ram              If the data should be stored in RAM.
  -b BATCH_SIZE, --batch_size BATCH_SIZE
                        Batch size to use during training.
  --epochs EPOCHS       Number of training epochs to do.
  -l LEARNING_RATE, --learning_rate LEARNING_RATE
                        Learning rate to use during training.
  -k K_FOLDS, --k_folds K_FOLDS
                        Folds to use in k-fold cross validation. 0 means don't use k-fold cross validation unless no validation dataset is provided, in which case k defaults to 3.
  --explainer_model EXPLAINER_MODEL
                        Which explainer type to use.
  --merge_rois          Merge ROIs together by specimen.
  --prune_misclassified
                        Remove entries for misclassified cell graphs when calculating separability scores.
  --output_prefix OUTPUT_PREFIX
                        Saves output files with this prefix, if provided.
  --upload_importances  Whether to upload importance scores to the database.
  --random_seed RANDOM_SEED
                        Random seed to use for reproducibility.
```

The main difference between the command line interface provided by [`cg-gnn`](https://pypi.org/project/cg-gnn/) and the SPT workflow interface is that parameters can't be eliminated from the config file for the latter. Instead,
* If you want to use the default value for a parameter, you must explicitly set it to that value.
* Boolean values must explicitly be set to `true` or `false` instead of simply including or omitting the parameter.
* `strata` can be set to `all` to use all strata (equivalent to not providing the parameter when using the CLI).
* `target_name` can be set to `none` to use all cells in the tissue sample (equivalent to not providing the parameter when using the CLI).

## Running the workflow

```sh
nextflow run .
```
