
Overview
--------
The ``spatial_profiling_toolbox`` (SPT) is:
  - a collection of modules that do image analysis computation in the context of
    histopathology, together with
  - a lightweight framework for deployment of a pipeline comprised of these
    modules in different runtime contexts (e.g. a High-Performance Cluster or on
    a single machine).


.. list-table::
   :widths: 2, 6, 2
   :header-rows: 1

   * - Computation module
     - Description
     - Original author
   * - Diffusion
     - The core of this module takes as input a collection of points, and generates the associated diffusion map and diffusion Markov chain, with the aim of producing features that are characteristic of the input geometry. Taken as a whole the diffusion analysis pipeline provides statistical test results and figures that assess the efficacy of diffusion-related metrics as discriminators of selected correlates.
     - Rami Vanguri
   * - Phenotype proximity
     - The core of this module takes as input two collections of points, and calculates the frequency with which a pair of points from the respective collections occur near each other. Taken as a whole the phenotype proximity analysis pipeline provides statistical test results and figures that assess the efficacy of proximity-related metrics as discriminators of selected correlates.
     - Rami Vanguri

.. image :: _static/example_diffusion_figure.png
   :target: _static/example_diffusion_figure.png

Preparing your data
-------------------

The current workflows all operate on spreadsheet files exported from the `HALO <https://indicalab.com/halo/>`_ software. Support for more generic inputs is in the works, but for now this means that you must use something like the metadata format exemplified by the `test data <https://github.com/nadeemlab/SPT/tree/main/spatial_profiling_toolbox/tests/data>`_. See also the `specification <https://github.com/nadeemlab/SPT/tree/main/schemas/file_manifest_specification_v0.5.md>`_ for the file manifest file.

Getting started
---------------

Install from `PyPI <https://pypi.org/project/spatialprofilingtoolbox/>`_::

    pip install spatial_profiling_toolbox

Use ``spt-pipeline`` to enter a dialog that solicits configuration parameters for your run. You will be given the option to run locally or to schedule the pipeline as `Platfrom LSF <https://www.ibm.com/products/hpc-workload-management>`_ jobs. In the LSF case, you must first build the library into a Singularity container by running ::

    cd building && ./build_singularity_container.sh

and moving the container (``.sif`` file) to an area accessible to the nodes in your cluster.

If you are doing computations with lots of data, the whole pipeline might take hours to complete. If you wish to see final results based on partially-complete intermediate data, use ``spt-analyze-results``.

Note that some of the utilities depend on a Linux/Unix/macOS environment.
