# Setting up `spt cggnn`

## 1. `explore-classes`

When working with a new dataset, start by running

```bash
spt cggnn explore-classes --spt_db_config_location <config_file_location> --study <study_name>
```

Given a configuration file of this format, where `...` is replaced with the relevant information to connect to your database instance,

```yaml
[database-credentials]
database = ...
endpoint =  ...
user = ...
password = ...
```

this will pull up a list of classes or that the tissue specimens associated with this study can be stratified into. For example, for the "Breast cancer IMC" study, this would look like

```bash
% spt cggnn explore-classes --spt_db_config_location 'spt_db.config' --study 'Breast cancer IMC'
   stratum identifier local temporal position indicator  subject diagnosed condition subject diagnosed result
0                   1               Before intervention  Response to hormone therapy               Refractory
1                   2               Before intervention  Response to hormone therapy                Sensitive
13                  3               Before intervention  Response to hormone therapy                Resistant
```

Note the stratum identifiers for strata you want to use, if it's not all of them. They'll be used in the data extraction process. Typically, you want to select classes that have a clear delineation to train a model on. For example, selecting only classes that are "Before intervention" if looking to predict if a patient will or won't respond to treatment. 


## 2. `extract`

Once you know what strata you want to keep, we'll run this command.

```bash
spt cggnn extract --spt_db_config_location <config_file_location> --study <study_name> --strata <strata_to_keep> --output_location <output_folder>
```

Given the strata you want to keep as an unadorned list of integers, e.g., `--strata 9 10` (this parameter can be skipped if you simply want all strata), this extracts single-cell data and strata/class information to three files in the output location/folder/directory you provide:
* `cells.h5`, a binary HDF5 file containing cell information at the individual cell level, such as its xy position, channel, and phenotype expressions, as a pandas DataFrame.
* `labels.h5`, a binary HDF file of a pandas DataFrame containing the class label of each tissue specimen as an integer ID, which is automatically derived from the strata information.
* `label_to_result.json` is a simple JSON that translates each label ID to a human-interpretable description, for use in visualizations after training.

These files can be used with the standalone `cg-gnn` pip package to create cell graphs, train a model on them, and generate summary statistics and graphs from the model.


## 3. `run`

`spt cggnn run` allows you to run the `cg-gnn` pip package directly from SPT. It combines `spt cggnn extract` with the entire `cggnn.run` process into a single command. As a result, it has many input parameters that need explaining.


### Required parameters

#### `spt_db_config_location`
Location of the SPT DB config file, as before.

#### `study`
Study name, as before.

#### `strata`

List of strata you want to keep by their ID, as space-separated integers, e.g., `--strata 9 10`, as before.


### Optional parameters

#### `validation_data_percent`

The *percent* of data you want to reserve for the validation set (e.g., provide 15 if you want 15\% of the data in the validation set).

The script creates potentially multiple regions of interest (ROIs) from each tissue specimen, but although ROIs are the base unit the model predicts, data is allocated to train/val/test sets by specimen and not individually so as to avoid sending information from the same tissue sample to different sets. The script will try allocate them so that there are approximately this percent of ROIs as validation data, but because of the variability in the number of ROIs per tissue sample there may be a significant difference between the given `validation_data_percent` and the actual amount in the validation set, especially in small datasets.

When set to 0, the model will automatically be set to use k-fold cross validation instead of a consistent validation set. I recommend doing this, and it's the default.

#### `test_data_percent`

The *percent* of data you want to reserve for the test set.

As with `validation_data_percent`, the script will try to allocate the data so that there are approximately this percent of ROIs as test data, but because of the variability in the number of ROIs per tissue sample there may be a significant difference between the two.

The default is set to 15 because we're usually working with smaller datasets.

#### `disable_channels`

If this parameter flag is provided, it instructs the model to not train on single cell channel information. Not recommended.

#### `disable_phenotypes`

If this parameter flag is provided, it instructs the model to not train on single cell phenotype information. Not recommended.

#### `roi_side_length`

The side length of the square ROIs to extract from each tissue sample, in pixels. This will vary depending on the resolution of the images, so I've added a new parameter that will automatically determine ROI size based on the average density of your tissue samples, so the default value is `None`. For "Melanoma intralesional IL2", I used to use 5,000, if I remember correctly.

#### `cells_per_slide_target`

The goal number of cells we want to have in each ROI we create. Combined with the average cell density across all tissue samples provided, this determines the ROI size. The default is 5,000 cells per slide, based on what I found to be a good number for "Melanoma intralesional IL2".

#### `target_name`

If given, build ROIs based only on cells with true values in this DataFrame column. If not provided, the script will use all cells in the tissue sample. 100,000 cells are chosen at random, and ROI boundaries are built on where these randomly selected cells are densest. (All cells within the bounding box go into the resulting ROI, the 100,000 cells are just used to determine where the ROI boundaries are.)

I generally use the cancer phenotype to build ROIs around, since that's what we're usually determing based on.

#### `in_ram`

Whether or not to load all data into RAM when training. I recommend this if you have enough RAM to fit the entire dataset since it makes training much faster.

#### `batch_size`

The batch size to use when training. The default is 1, since our datasets are usually very small.

#### `epochs`

The number of epochs to train for. This doesn't take into account how many k-folds you do, so generally you should multiple epochs by the number of folds for a more accurate interpretation. The default is 5, to go along with the default number of folds, and it's probably still more than necessary.

#### `learning_rate`

The learning rate to use when training. The default is 1e-3, although sometimes I use even smaller values if validation accuracy falls off early in the epochs. I do not recommend going up from this value.

#### `k_folds`

The number of folds to use in k-fold cross validation. 0 means don\'t use k-fold cross validation unless no validation dataset is provided, in which case k defaults to 3. Don't use too many folds if the training set is small, because the validation set will be the reciprocal of the number of folds you specify.

#### `explainer_model`

Which explainer type to use. `pp` is default, as it's the only type that supports all explainibility metrics. I've yet to experiment thoroughly with other options.

#### `merge_rois`

Whether or not to merge ROIs from the same tissue sample into a single ROI when outputting graphs and metrics. Recommended, as it makes them easier to understand, at the cost of mucking up some theoretical backing of things like how importance scores are calculated.

#### `prune_misclassified`

Whether or not to prune misclassified ROIs from summary statistics. Not recommended unless you're very, very confident about the accuracy of your model, since it often results in you removing an entire class from your data which results in division by 0 errors. Probably okay for "Melanoma intralesional IL2" and maybe "Urolthelial ICI", but definitely not for the other datasets, for which the model is usually no better than random.

#### `output_prefix`

The prefix to use for all output files:
* `<prefix>_model.pt`, which can be used to recreate the trained model
* `<prefix>_importances.csv`, a CSV of the importance scores for each cell present in any ROI, indexed by its histological structure ID.

If not provided, no files will be output.

#### `upload_importances`

Whether to upload importance scores calculated by the model to the database the data was extracted from. Recommend not doing so unless you're very confident in your model parameters.


## 4. `cggnn` as an SPT workflow

When `cggnn` is run as an SPT workflow, a few parameters are made unavailable in order to maximize ease of running with Nextflow. The parameters that do remain are the ones I recommend controlling SPT with.

Unlike other SPT workflows, these parameters are provided to the software primarily by a workflow configuration file, which has the following parameters:

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

Note that, unlike with the CLI, parameters can't be eliminated from the config file. If you want to use the default value for a parameter, you must explicitly set it to that value,  and boolean values must be set to `true` or `false` instead of simply omitting the parameter.

Other special cases:
* `strata` can be set to `all` to use all strata (equivalent to not providing the parameter when using the CLI).
* `target_name` can be set to `none` to use all cells in the tissue sample (equivalent to not providing the parameter when using the CLI).
