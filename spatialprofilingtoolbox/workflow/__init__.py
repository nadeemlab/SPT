"""
Each of the workflow subpackages contains the implementation details for one full pipeline.
They are:

1. A **job generator**. This writes the scripts that will run in the chosen runtime context
   (High-Performance Computing cluster, local, etc.).
2. The **core**. This represents one job's worth of computational work. This is ideally independent
   of file system and runtime context, such that a user of the library may use the main calculations
   to fit their own needs.
3. An **integrator**. This is the part of the pipeline that will run after any large-scale parallel
  jobs have completed. It is also potentially run *before* all such jobs have completed, to provide
  early final results on partial data.
4. The **computational design**. This is where idiosyncratic configuration parameters specific to
this pipeline are stored and managed.
"""
import importlib
__version__ = '0.5.0'

workflow_names_and_subpackages = {
    'tabular import': 'tabular_import',
    'phenotype proximity': 'phenotype_proximity',
}


def get_workflow_names():
    return list(workflow_names_and_subpackages.keys())


def get_workflow(workflow_name):
    subpackage_name = workflow_names_and_subpackages[workflow_name]
    subpackage = importlib.import_module(f'.{subpackage_name}', __name__)
    return subpackage.components
