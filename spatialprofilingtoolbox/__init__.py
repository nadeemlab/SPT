#!/usr/bin/env python3
"""
This is the Spatial Profiling Toolbox package. The source code is available
`here <https://github.com/nadeemlab/SPT>`_.
"""

from .workflows import workflows
from .workflows import workflow_names
from .environment.configuration_settings import get_version

# from .environment.skimmer import DataSkimmer
from .environment.logging.log_formats import colorized_logger
logger = colorized_logger(__name__)

__version__ = get_version()

# def get_semantic_source_parser(workflow=None, **kwargs):
#     s = 'skip_semantic_parse'
#     if s in kwargs:
#         skip_semantic_parse = kwargs[s]
#     else:
#         skip_semantic_parse = None
#     return DataSkimmer(
#         dataset_design = get_dataset_design(workflow=workflow, **kwargs),
#         input_path = kwargs['input_path'],
#         file_manifest_file = kwargs['file_manifest_file'],
#         skip_semantic_parse = skip_semantic_parse,
#     )

def get_dataset_design(workflow=None, **kwargs):
    """
    Exposes design parameters to scripts.
    """
    if workflow in workflows:
        return workflows[workflow].dataset_design(**kwargs)
    else:
        logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError

def get_computational_design(workflow=None, **kwargs):
    """
    Exposes design parameters to scripts.
    """
    if workflow in workflows:
        ComputationalDesign = workflows[workflow].computational_design
    else:
        logger.error('Workflow "%s" not supported.', str(workflow))
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
        logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError

def get_integrator(workflow=None, **kwargs):
    """
    Exposes pipeline analysis integrators to scripts.
    """
    if workflow in workflows:
        computational_design = get_computational_design(workflow = workflow, **kwargs)

        Integrator = workflows[workflow].integrator
        return Integrator(
            computational_design = computational_design,
            **kwargs,
        )
    else:
        logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError
