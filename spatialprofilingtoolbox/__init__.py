#!/usr/bin/env python3
"""
This is the Spatial Profiling Toolbox package. The source code is available
`here <https://github.com/nadeemlab/SPT>`_.
"""

from .workflows import workflows
from .workflows import workflow_names
from .environment.configuration_settings import get_version

from .environment.logging.log_formats import colorized_logger
logger = colorized_logger(__name__)

__version__ = get_version()

def get_dataset_design(workflow=None, **kwargs):
    """
    Exposes design parameters to scripts.
    """
    return workflows[workflow].dataset_design(**kwargs)

def get_computational_design(workflow=None, **kwargs):
    """
    Exposes design parameters to scripts.
    """
    ComputationalDesign = workflows[workflow].computational_design
    dataset_design = get_dataset_design(workflow = workflow, **kwargs)
    computational_design = ComputationalDesign(dataset_design = dataset_design, **kwargs)
    return computational_design

def get_initializer(workflow=None, **kwargs):
    """
    Exposes pipeline initializer to scripts.
    """
    dataset_design = get_dataset_design(workflow = workflow, **kwargs)
    computational_design = get_computational_design(workflow = workflow, **kwargs)
    Initializer = workflows[workflow].initializer
    return Initializer(
        dataset_design = dataset_design,
        computational_design = computational_design,
        **kwargs,
    )

def get_core_job(workflow=None, **kwargs):
    """
    Exposes pipeline core jobs to scripts.
    """
    dataset_design = get_dataset_design(workflow = workflow, **kwargs)
    computational_design = get_computational_design(workflow = workflow, **kwargs)
    CoreJob = workflows[workflow].core_job
    return CoreJob(
        dataset_design = dataset_design,
        computational_design = computational_design,
        **kwargs,
    )

def get_integrator(workflow=None, **kwargs):
    """
    Exposes pipeline analysis integrators to scripts.
    """
    computational_design = get_computational_design(workflow = workflow, **kwargs)

    Integrator = workflows[workflow].integrator
    return Integrator(
        computational_design = computational_design,
        **kwargs,
    )
