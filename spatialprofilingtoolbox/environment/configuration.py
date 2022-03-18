"""
Provides workflow definitions in terms of implementation classes, and
configuration parameter management.
"""
import importlib.resources
import os
from os.path import abspath
from os.path import exists
from os.path import join
import json

from ..applications.configuration_ui.ui import configuration_dialog
from .configuration_settings import config_filename
from .configuration_settings import get_version

from .log_formats import colorized_logger
logger = colorized_logger(__name__)

nf_script_file = 'spt_pipeline.nf'
nf_config_file = {
    'lsf' : 'nextflow.config.lsf',
    'local' : 'nextflow.config.local',
}

def write_out_nextflow_script():
    for filename in [nf_script_file] + list(nf_config_file.values()):
        contents = None
        with importlib.resources.path('spatialprofilingtoolbox', filename) as path:
            with open(path, 'rt') as file:
                contents = file.read().rstrip('\n')
        if contents:
            if not exists(join(os.getcwd(), filename)):
                with open(join(os.getcwd(), filename), 'wt') as file:
                    file.write(contents)
        else:
            logger.error('Could not load %s', filename)

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
        configuration_dialog()
        json_string = open(config_filename, 'rt').read()

    if (not supplied_json_string) and has_config_file:
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
