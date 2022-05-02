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
import re

from .configuration_settings import config_filename
from .configuration_settings import get_version
from .extract_compartments import extract_compartments
from .settings_wrappers import DatasetSettings

from .log_formats import colorized_logger
logger = colorized_logger(__name__)

nf_script_file = 'spt_pipeline.nf'
nf_config_file = {
    'lsf' : 'nextflow.config.lsf',
    'local' : 'nextflow.config.local',
}

def write_out_nextflow_script(sif_file, excluded_host_name=None, parameters={}):
    if parameters != {}:
        contents = None
        with importlib.resources.path('spatialprofilingtoolbox', nf_script_file) as path:
            with open(path, 'rt') as file:
                contents = file.read().rstrip('\n')
        if contents:
            if not exists(join(os.getcwd(), nf_script_file)):
                workflow_='{{ workflow }}'
                input_path_='{{ input_path }}'
                skip_semantic_parse='{{ skip_semantic_parse }}'

                contents = re.sub('{{ workflow }}', parameters['workflow'], contents)
                contents = re.sub('{{ input_path }}', parameters['input_path'], contents)
                if not 'skip_semantic_parse' in parameters:
                    parameters['skip_semantic_parse'] = 'false'
                else:
                    parameters['skip_semantic_parse'] = 'true' if (parameters['skip_semantic_parse'] == True or parameters['skip_semantic_parse'] == 'true') else 'false'
                contents = re.sub('{{ skip_semantic_parse }}', parameters['skip_semantic_parse'], contents)

                with open(join(os.getcwd(), nf_script_file), 'wt') as file:
                    file.write(contents)
        else:
            logger.error('Could not load %s', nf_script_file)

    for filename in list(nf_config_file.values()):
        contents = None
        with importlib.resources.path('spatialprofilingtoolbox', filename) as path:
            with open(path, 'rt') as file:
                contents = file.read().rstrip('\n')
        if contents:
            if not exists(join(os.getcwd(), filename)):
                if sif_file:
                    contents = re.sub("'spt_latest\.sif'", "'" + sif_file + "'", contents)
                if filename == 'nextflow.config.lsf':
                    if not excluded_host_name is None:
                        contents = re.sub('{{ host_to_exclude }}', excluded_host_name, contents)
                        contents = re.sub('// process {', 'process {', contents)
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
        raise Exception('Deprecation of configuration dialog')

    if (not supplied_json_string) and has_config_file:
        json_string = open(config_filename, 'rt').read()

    parameters = json.loads(json_string)

    if not 'file_manifest_file' in parameters:
        parameters['file_manifest_file'] = 'file_manifest.tsv'

    return parameters
