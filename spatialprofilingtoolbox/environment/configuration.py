"""
Provides workflow definitions in terms of implementation classes, and
configuration parameter management.
"""
import importlib.resources
import os
from os.path import exists, abspath
import json

from .workflow_modules import WorkflowModules
from ..workflows.diffusion import components as diffusion_workflow
from ..workflows.phenotype_proximity import components as phenotype_proximity_workflow
from ..workflows.front_proximity import components as front_proximity_workflow
from ..workflows.density import components as density_workflow

from .log_formats import colorized_logger
logger = colorized_logger(__name__)

config_filename = '.spt_pipeline.json'

workflows = {
    **diffusion_workflow,
    **phenotype_proximity_workflow,
    **front_proximity_workflow,
    **density_workflow,
}

def get_version():
    with importlib.resources.path('spatialprofilingtoolbox', 'version.txt') as path:
        with open(path, 'r') as file:
            version = file.read().rstrip('\n')
    return version

def get_config_parameters(json_string=None):
    supplied_json_string = not json_string is None
    has_config_file = exists(config_filename)

    if supplied_json_string and has_config_file:
        logger.error(
            'Configuration file %s exists, but you are also supplying json_string.',
            config_filename,
        )
        return None

    if (not supplied_json_string) and (not has_config_file):
        logger.error(
            ''.join([
                'Configuration file %s does not exist, and you did not supply ',
                'json_string. Try spt-configu'
            ]),
            config_filename
        )
        return None

    if has_config_file:
        json_string = open(config_filename, 'rt').read()

    parameters = json.loads(json_string)

    version_specifier = 'spt_version'
    if version_specifier in parameters:
        if parameters[version_specifier] != get_version():
            logger.debug(
                'Version mentioned in configuration file is %s, but running version of SPT is %s.',
                parameters[version_specifier],
                get_version(),
            )

    return parameters
