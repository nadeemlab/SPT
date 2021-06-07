
# Documentation for users

The `spatial-analysis-toolbox` (SAT) is:
  - a collection of modules that do image analysis computation in the context of histopathology, together with
  - a lightweight framework for deployment of a pipeline comprised of these modules in different runtime contexts (e.g. a High-Performance Cluster or on a single machine).

# Getting started

Clone the repository, and install the Python package with `pip`:

```
pip install spatial_analysis_toolbox/
```

Then run `sat-pipeline` to enter a dialog that configures the parameters for your run. You will be given the option to run locally or to schedule the pipeline as [Platfrom LSF (Load Sharing Facility)](https://www.ibm.com/products/hpc-workload-management) jobs. In the LSF case, you must first build the library into a Singularity container by running `cd building && ./build_singularity_container.sh`.

If you are doing computations with lots of data, the whole pipeline might take hours to complete. If you wish to see final results based on partially-complete intermediate data, use `sat-analyze-results`.

# Platform

Some of the utilities depend on a Linux/Unix/macOS environment.

# Customization

See [Documentation for Developers](spatial_analysis_toolbox/README.md).
