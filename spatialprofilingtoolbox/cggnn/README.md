# cggnn

This module constructs cell graphs and uses neural networks on the created graphs to predict outcomes of your choice. It's dependent on the [cg-gnn on pip](https://github.com/CarlinLiao/cg-gnn).

## Installation

In addition to the dependencies listed in `pyproject.yml`, you'll also need to install platform-specific versions of [PyTorch](https://pytorch.org/get-started/locally/) and [DGL](https://www.dgl.ai/pages/start.html) separately, and ideally [cudatoolkit](https://anaconda.org/nvidia/cudatoolkit) if your system supports it.

## Credits

This module is a heavily modified version of [the histocartography project](https://github.com/BiomedSciAI/histocartography) and one of its applications: [hact-net](https://github.com/histocartography/hact-net). Specifically,

* Cell graph formatting, saving, and loading using DGL is patterned on how they were implemented in hact-net
* A few data utility functions, including `CGDataset` and `collate`, have only minor modifications from their source in hact-net
* The dependence on histocartography is indirect, through the functionality used by the above features
