# Using `spt cggnn`

The intended procedure for using `spt cggnn` (**c**ell **g**raph - **g**raph **n**eural **n**etwork) is:
1. Explore the data available for the study of your choice and train the model.
   1. Evaluate the specimen cohorts at your disposal with `spt cggnn explore-classes`.
   2. Now that you know which specimen cohorts ("strata") you want to use, fetch the relevant data artifacts from SPT using `spt cggnn extract`.
   3. Artifacts in hand, use `spt cggnn run` or the `cg-gnn` pip package directly to train and fine-tune your CG-GNN model.
2. Given that you now know the parameters you used to arrive at your fine-tuned CG-GNN model, use `spt workflow configure` to create artifacts that will reproducibly* run through the entire process of gathering the data for, training, and reporting with your trained model. Then, your workflow can be run in one line using Nextflow to approximately reproduce your model and results.

This document will go into more detail on the second step.

\* _Because the GNN uses non-deterministic algorithms, workflows will not be exactly reproducible._

## Configuring the cggnn workflow with `spt workflow configure`

To configure the `cggnn` SPT workflow, you must provide the following parameters as follows:

```
spt workflow configure --local --workflow='cggnn' --study-name=... --database-config-file=... --workflow-config-file=...
```

For canonical explanations of each parameter, please refer to the docstrings of the scripts being called by `spt workflow configure`, as shown by [the Nextflow file used for cggnn](spatialprofilingtoolbox/workflow/assets/cggnn.nf), and the [`cg-gnn` pip package](https://pypi.org/project/cg-gnn/) documentation. The definitions provided for quick reference only and may not be the most updated.

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
upload_importances = ...
```

Note that with this configuration file, parameters can't be eliminated to use the default value as is possible with CLI arguments.

* `strata`: Specimen strata to use as labels, identified according to the "stratum identifier" in `explore-classes`. This should be given as space separated integers. Can be set to `all` to use all strata.
* `validation_data_percent`: Percentage of data to use as validation data. Set to 0 if you want to do k-fold cross-validation. (Training percentage is implicit.)
* `test_data_percent`: Percentage of data to use as the test set. (Training percentage is implicit.)
* `disable_channels`: If true, disable the use of channel information in the graph.
* `disable_phenotypes`: If true, disable the use of phenotype information in the graph.
* `cells_per_slide_target`: Used with the median cell density across all slides to determine the ROI size.
* `target_name`: Build ROIs based only on cells with true values in this DataFrame column. Can be set to `none` to use all cells in the tissue sample.
* `in_ram`: If true, store the data in RAM.
* `batch_size`: Batch size to use during training.
* `epochs`: Number of training epochs to do.
* `learning_rate`: Learning rate to use during training.
* `k_folds`: Folds to use in k-fold cross validation. 0 means don't use k-fold cross validation unless no validation dataset is provided, in which case k defaults to 3.
* `explainer_model`: Which explainer type to use. If not `none`, importance scores will be calculated using the model archetype chosen. `pp` is recommended.
* `merge_rois`: If true, return a CSV of importance scores merged together by specimen.
* `upload_importances`: Whether to upload importance scores to the database.
* `random_seed`: Random seed to use for reproducibility. Can be set to `none` if you don't wish to use a random seed.

## Running the workflow

```sh
nextflow run .
```

In the event that you'd like to run the cggnn workflow on different hardware than where you created it, the [`cggnn_environment.yml`](cggnn_environment.yml) file in this directory installs the minimum dependencies required to run the workflow fluidly. The environment assumes the machine you're running the workflow on has a CUDA-compatible GPU. We don't recommend running the cggnn workflow without it, but if you choose to do so, you will need to remove mentions of CUDA from the environment file. If your machine does support CUDA but not CUDA 11.8, you will need to change the version used by CUDA, pytorch, and DGL to a version your GPU supports.

Assuming you have conda installed [(instructions here)](https://conda.io/projects/conda/en/latest/user-guide/install/index.html), create the environment and activate it with the following commands:

```sh
conda env create -f docs/cggnn_environment.yml
conda activate spt_cggnn
```
