# Documentation for developers


## How to create a new module

For a new computation module:
  1. Make a new subdirectory under `computation_modules`. Mimicing the overall design of the existing modules is a reasonable start. Freely use the `environment/` functionality.
  2. Update the packages list in `setup.py` if necessary.
  3. Add a new workflow entry to `configuration.py`.
  4. Update `sat-pipeline` to solicit any new configuration parameters that will be needed.
  5. Create a script in `bin/`, mimicing `spt_diffusion_analysis.py` etc., to be run by single processes/jobs. This can be regarded as exposing API from your Python module to your system environment via a CLI.
  6. (Optional) Update `sat-analyze-results` to include your new workflow's final steps.
  7. Add unit tests to `tests/`.
  8. Heed the results of `pytest` or `coverage` before pushing new commits or submitting a pull request, especially if your addition required modification of existing modules. (\* Currently only integration tests are available, one for each workflow.)

If you find that a large piece of what you need to implement is already present in an existing module, see if you can take that work out of the existing module and place it either in a module of its own or in the `environment/` area. The `environment/` area is intended for utilities, with few dependencies of their own, which might be useful to a large number of first-class, more specific modules.


## Testing

If you experiment with the code locally, you can run the integration tests

```
cd spatial_profiling_toolbox/tests/
./test_diffusion_pipeline.sh
```

```
cd spatial_profiling_toolbox/tests/
./test_proximity_pipeline.sh
```

and inspect the results to verify that basic functionality remains intact.

Unit tests are planned for the existing codebase.


## Generating detailed documentation

See [docs/](docs/).
