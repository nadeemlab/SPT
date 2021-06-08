# Documentation for developers

The `spatial-analysis-toolbox` is a collection of modules that do image analysis computation in the context of histopathology, and a lightweight framework for deployment of a pipeline comprised of these modules in different runtime contexts (e.g. a High-Performance Cluster or on a single machine).

# Library layout

```
spatial_analysis_toolbox/
├── api.py
├── computation_modules
│   ├── diffusion
│   │   ├── analyzer.py
│   │   ├── computational_design.py
│   │   ├── integrator.py
│   │   └── job_generator.py
│   └── phenotype_proximity
│       ├── analyzer.py
│       ├── computational_design.py
│       ├── integrator.py
│       └── job_generator.py
├── dataset_designs
│   └── multiplexed_immunofluorescence
│       └── design.py
└── environment
    ├── computational_design.py
    ├── configuration.py
    ├── database_context_utility.py
    ├── job_generator.py
    ├── log_formats.py
    ├── pipeline_design.py
    └── single_job_analyzer.py
bin
├── sat-analyze-results
├── sat-cell-phenotype-proximity-analysis.py
├── sat-diffusion-analysis.py
├── sat-generate-jobs.py
├── sat-pipeline
└── sat-print.py
```

# How to create a new module

For a new computation module:
  1. Make a new subdirectory under `computation_modules`. Mimicing the overall design of the existing modules is a reasonable start. Freely use the `environment/` functionality.
  2. Add a new workflow entry to `configuration.py`.
  3. Update `sat-pipeline` to solicit any new configuration parameters that will be needed.
  4. (Optional) Update `sat-analyze-results` to include your new workflow's final steps.
  5. Add unit tests to `tests/`.
  6. Heed the results of `pytest` or `coverage` before pushing new commits or submitting a pull request, especially if your addition required modification of existing modules. (\* Currently only integration tests are available, one for each workflow.)

If you find that a large piece of what you need to implement is already present in an existing module, see if you can take that work out of the existing module and place it either in a module of its own or in the `environment/` area. The `environment/` area is intended for utilities, with few dependencies of their own, which might be useful to a large number of first-class, more specific modules.


# Testing

If you experiment with the code locally, you can run the integration tests

```
cd spatial_analysis_toolbox/tests/
./test_diffusion_pipeline.sh
```

```
cd spatial_analysis_toolbox/tests/
./test_proximity_pipeline.sh
```

and inspect the results to verify that basic functionality remains intact.

Unit tests are planned for the existing codebase.
