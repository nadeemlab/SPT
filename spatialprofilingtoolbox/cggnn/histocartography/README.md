# Histocartography for SPT

This submodule of SPT contains a library to train a graph neural network model on graphs built out of cell spatial data to predict an outcome variable. In addition to standalone use, it also serves as an example implementation of an SPT-compatible graph neural network pipeline, for open source developers to reference when implementing their own deep learning tools that use cell graphs created by SPT. The key features that such an implementation must have are:
1. model training and inference
2. cell-level importance score calculation

If the input and output schema is followed, your tool will be compatible with the SPT ecosystem, allowing users to easily integrate your tool into their SPT workflows and upload your model's results to an SPT database.

This submodule is a heavily modified version of [histocartography](https://github.com/BiomedSciAI/histocartography) and two of its applications, [hact-net](https://github.com/histocartography/hact-net) and [patho-quant-explainer](https://github.com/histocartography/patho-quant-explainer). For this reason, it is less tested and is held to a different style standard than the rest of the library.

## Quickstart

Use [`spt cggnn extract` and `spt cggnn generate-graphs`](https://github.com/nadeemlab/SPT/tree/main/spatialprofilingtoolbox/cggnn) to create cell graphs from a SPT database instance that this submodule can use.

This module includes two scripts that you can call from the command line, or you can use the modules directly in Python.
1. `spt cggnn train` trains a graph neural network model on a set of cell graphs, saves the model to file, and updates the cell graphs it was trained on with cell-level importance-to-classification scores if an explainer model type is provided.
2. `spt cggnn separability` calculates class separability metrics given a trained model and other metadata.

## Credits

This submodule is a heavily modified version of [the histocartography project](https://github.com/BiomedSciAI/histocartography) and two of its applications: [hact-net](https://github.com/histocartography/hact-net) and [patho-quant-explainer](https://github.com/histocartography/patho-quant-explainer). Specifically:

* Cell graph formatting, saving, and loading using DGL is patterned on how they were implemented in hact-net.
* The neural network training and inference module is modified from the hact-net implementation for cell graphs.
* Importance score and separability calculations are sourced from patho-quant-explainer.
* The dependence on histocartography is indirect, through the functionality used by the above features.

Due to dependency issues that arose when using the version of histocartography published on PyPI, we've chosen to copy and make slight updates to only the modules of histocartography used by the features supported in this library. The version control history of this specific branch prior to inclusion in the main body of SPT can be found [here](https://github.com/CarlinLiao/cg-gnn). We would prefer to deprecate some or all of this submodule in favor of dependency on the histocartography package released on PyPI, but currently it is necessary to use the functionality in this incorporated and modified form.
