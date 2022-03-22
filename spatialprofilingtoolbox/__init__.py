#!/usr/bin/env python3
"""
This is the Spatial Profiling Toolbox package. The source code is available
`here <https://github.com/nadeemlab/SPT>`_.
"""

from .environment.configuration_settings import config_filename
from .environment.configuration_settings import workflows
from .environment.configuration_settings import get_version
from .environment.configuration import get_config_parameters
from .environment.configuration import write_out_nextflow_script
from .environment.configuration import nf_script_file
from .environment.configuration import nf_config_file
from .applications.configuration_ui.ui import configuration_dialog

from .environment.settings_wrappers import DatasetSettings
from .environment.log_formats import colorized_logger
__logger = colorized_logger(__name__)

__version__ = get_version()

def get_job_generator(workflow=None, **kwargs):
    """
    Exposes job generators to scripts.
    """
    if workflow in workflows:
        dataset_design_class = get_dataset_design_class(workflow = workflow, **kwargs)

        Generator = workflows[workflow].generator
        return Generator(
            dataset_design_class = dataset_design_class,
            **kwargs,
        )
    else:
        __logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError

def get_dataset_design_class(workflow=None, **kwargs):
    return workflows[workflow].dataset_design

def get_dataset_design(workflow=None, **kwargs):
    """
    Exposes design parameters to scripts.
    """
    if workflow in workflows:
        return workflows[workflow].dataset_design(**kwargs)
    else:
        __logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError

def get_computational_design(workflow=None, **kwargs):
    """
    Exposes design parameters to scripts.
    """
    if workflow in workflows:
        ComputationalDesign = workflows[workflow].computational_design
    else:
        __logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError

    dataset_design = get_dataset_design(workflow = workflow, **kwargs)
    computational_design = ComputationalDesign(dataset_design = dataset_design, **kwargs)
    return computational_design

def get_analyzer(workflow=None, **kwargs):
    """
    Exposes pipeline analyzers to scripts.
    """
    if workflow in workflows:
        dataset_design = get_dataset_design(workflow = workflow, **kwargs)
        computational_design = get_computational_design(workflow = workflow, **kwargs)
        Analyzer = workflows[workflow].analyzer
        return Analyzer(
            dataset_design = dataset_design,
            computational_design = computational_design,
            **kwargs,
        )
    else:
        __logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError

def get_dataset_settings(**kwargs):
    return DatasetSettings(
        kwargs['input_path'],
        kwargs['file_manifest_file'],
    )

def get_integrator(workflow=None, **kwargs):
    """
    Exposes pipeline analysis integrators to scripts.
    """
    if workflow in workflows:
        dataset_settings = get_dataset_settings(**kwargs)
        computational_design = get_computational_design(workflow = workflow, **kwargs)

        Integrator = workflows[workflow].integrator
        return Integrator(
            dataset_settings = dataset_settings,
            computational_design = computational_design,
            **kwargs,
        )
    else:
        __logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError
