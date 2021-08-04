#!/usr/bin/env python3
"""
This is the Spatial Profiling Toolbox package. The source code is available
`here <https://github.com/nadeemlab/SPT>`_.
"""

from .applications.diffusion_graphs_viz.diffusion_graphs_viz import DiffusionGraphsViz
from .applications.diffusion_tests_viz import DiffusionTestsViz
from .applications.front_proximity_viz import FrontProximityViz
from .environment.configuration import get_config_parameters
from .environment.configuration import get_config_parameters_from_file
from .environment.configuration import config_filename
from .environment.configuration import workflows
from .environment.configuration import get_version

from .environment.settings_wrappers import JobsPaths, DatasetSettings
from .environment.log_formats import colorized_logger
__logger = colorized_logger(__name__)

__version__ = get_version()

def get_job_generator(workflow=None, **kwargs):
    """
    Exposes job generators to scripts.
    """
    if workflow in workflows:
        return workflows[workflow].generator(**kwargs)
    else:
        __logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError

def get_dataset_design(workflow=None):
    """
    Exposes design parameters to scripts.
    """
    if workflow in workflows:
        return workflows[workflow].dataset_design
    else:
        __logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError

def get_computational_design(workflow=None):
    """
    Exposes design parameters to scripts.
    """
    if workflow in workflows:
        return workflows[workflow].computational_design
    else:
        __logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError

def get_analyzer(workflow=None, **kwargs):
    """
    Exposes pipeline analyzers to scripts.
    """
    if workflow in workflows:
        elementary_phenotypes_file = kwargs['elementary_phenotypes_file']
        complex_phenotypes_file = kwargs['complex_phenotypes_file']
        del kwargs['elementary_phenotypes_file']
        del kwargs['complex_phenotypes_file']

        DatasetDesign = get_dataset_design(workflow = workflow)
        Analyzer = workflows[workflow].analyzer
        return Analyzer(
            dataset_design = DatasetDesign(
                elementary_phenotypes_file = elementary_phenotypes_file,
            ),
            complex_phenotypes_file = complex_phenotypes_file,
            **kwargs,
        )
    else:
        __logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError

def get_integrator(workflow=None, **kwargs):
    """
    Exposes pipeline analysis integrators to scripts.
    """
    if workflow in workflows:
        DatasetDesign = get_dataset_design(workflow = workflow)
        ComputationalDesign = get_computational_design(workflow = workflow)
        Integrator = workflows[workflow].integrator
        return Integrator(
            jobs_paths = JobsPaths(
                kwargs['job_working_directory'],
                kwargs['jobs_path'],
                kwargs['logs_path'],
                kwargs['schedulers_path'],
                kwargs['output_path'],
            ),
            dataset_settings = DatasetSettings(
                kwargs['input_path'],
                kwargs['file_manifest_file'],
                kwargs['outcomes_file'],
            ),
            computational_design = ComputationalDesign(
                dataset_design = DatasetDesign(
                    kwargs['elementary_phenotypes_file'],
                ),
                complex_phenotypes_file = kwargs['complex_phenotypes_file'],
            ),
        )
    else:
        __logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError
