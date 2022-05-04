"""
Each of these subpackages contains the implementation details for one full pipeline, consisting of:

1. A **job generator**. This writes the scripts that will run in the chosen runtime context (High-Performance Computing cluster, local, etc.).
2. A so-called **analyzer**. This represents one job's worth of computational work.
3. The **core**. This is ideally independent of file system and runtime context, such that a user of the library may use the main calculations to fit their own needs.
4. An **integrator**. This is the part of the pipeline that will run after any large-scale parallel jobs have completed. It is also potentially run *before* all such jobs have completed, to provide early final results on partial data.
5. The **computational design**. This is where idiosyncratic configuration parameters specific to this pipeline are stored and managed.
"""
import importlib
from setuptools import find_packages
import os
from os.path import dirname

subpackages = {
    name : importlib.import_module('.%s' % name, __name__)
    for name in find_packages(where=dirname(__file__))
}
workflow_components = [
    getattr(subpackage, 'components')
    for name, subpackage in subpackages.items()
]
workflow_names = [list(d.keys())[0] for d in workflow_components]
workflows = {
    key : [d[key] for d in workflow_components if key in d][0]
    for key in workflow_names
}
