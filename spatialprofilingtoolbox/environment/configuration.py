"""
Provides workflow definitions in terms of implementation classes, and configuration parameter management.
"""
import importlib.resources
import sys
import argparse
import configparser
import os
from os import getcwd
from os.path import exists
import re
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

def get_config_parameters_from_file():
    """
    Retrieves previously-serialized configuration parameters from file.

    :return: The parameters.
    :rtype: dict
    """
    # config = configparser.ConfigParser()
    # config.read(config_filename)
    # parameters = dict(config['default'])
    parameters = json.load(config_filename)
    # version = dict(config['static'])['version']
    if 'SPT version' in parameters:
        version = parameters['SPT version']
        if version != get_version():
            logger.warning(
                'The version of this running instance of SPT (%s) does not match the version that generated configuration file (namely %s).',
                get_version(),
                version,
            )

    # bool_parameters = [
    #     'skip_integrity_check',
    #     'balanced',
    #     'save_graphml',
    #     'use_intensities',
    #     'dichotomize',
    # ]
    # for name in bool_parameters:
    #     if name in parameters and parameters[name] == 'True':
    #         parameters[name] = True
    #     else:
    #         parameters[name] = False

    # if 'compartments' in parameters:
    #     compartments = parameters['compartments']
    #     if compartments != '':
    #         compartments_list = [c.strip(' ') for c in compartments.split(',')]
    #         parameters['compartments'] = compartments_list

    return parameters

def get_version():
    with importlib.resources.path('spatialprofilingtoolbox', 'version.txt') as path:
        with open(path, 'r') as file:
            version = file.read().rstrip('\n')
    return version

def write_config_parameters_to_file(parameters):
    """
    Serializes configuration parameters to file, using a singleton pattern.

    Args:
        parameters (dict):
            Key-value pairs to record. Typically these are keyword arguments for the
            classes constructed at initialization time for entry points into the
            pipelines/workflows.
    """
    config = configparser.ConfigParser()
    if 'compartments' in parameters:
        compartments = parameters['compartments']
        if compartments != '':
            compartments_list = [c.strip(' ') for c in compartments.split(',')]
            parameters['compartments'] = compartments_list

    config['default'] = parameters
    config['static'] = {'version' : get_version()}
    with open(config_filename, 'w') as file:
        config.write(file)

def get_config_parameters_from_cli():
    parser = argparse.ArgumentParser(
        description = ''.join([
            'This script generates jobs to be run optionally on an HPC ',
            '(High-Performance Computing) cluster using IBM\'s Platform LSF ',
            '(Load Sharing Facility), and the commands to schedule them or run them locally. ',
            'The jobs do calculations with histology images.',
        ])
    )
    parser.add_argument('--sif-file',
        dest='sif_file',
        type=str,
        required=True,
        help='',
    )
    parser.add_argument('--computational-workflow',
        dest='computational_workflow',
        type=str,
        required=True,
        help='',
    )
    parser.add_argument('--input-path',
        dest='input_path',
        type=str,
        required=True,
        help='Path to input files.',
    )
    parser.add_argument('--outcomes-file',
        dest='outcomes_file',
        type=str,
        required=True,
        help='Path to tabular file containing a column of sample identifiers and a column of outcome assignments.',
    )
    parser.add_argument('--output-path',
        dest='output_path',
        type=str,
        required=True,
        help='Where jobs should write their output.',
    )
    parser.add_argument('--jobs-path',
        dest='jobs_path',
        type=str,
        required=True,
        help='Where jobs themselves should be written.',
    )
    parser.add_argument('--schedulers-path',
        dest='schedulers_path',
        type=str,
        required=True,
        help='Where job scheduling scripts should be written.',
    )
    parser.add_argument('--file-manifest',
        dest='file_manifest_file',
        type=str,
        required=True,
        help='File containing metadata for each source file. Format should be "BCDC11v5".',
    )
    parser.add_argument('--runtime-platform',
        dest='runtime_platform',
        type=str,
        required=True,
        help='Either "lsf" (for HPC runs) or "local".',
    )
    parser.add_argument('--elementary-phenotypes-file',
        dest='elementary_phenotypes_file',
        type=str,
        required=True,
        help='File containing metadata about the channels/observed phenotypes.',
    )
    parser.add_argument('--complex-phenotypes-file',
        dest='complex_phenotypes_file',
        type=str,
        required=True,
        help='File specifying signatures for phenotype combinations of interest.',
    )
    parser.add_argument('--logs-path',
        dest='logs_path',
        type=str,
        required=True,
        help='Path to logs.',
    )
    parser.add_argument('--excluded-hostname',
        dest='excluded_hostname',
        type=str,
        required=True,
        help='The name of a host to exclude for deployment (e.g. a control node).',
    )
    parser.add_argument('--skip-integrity-check',
        dest='skip_integrity_check',
        type=str,
        required=True,
        help='Whether to skip calculation of input file checksums in some cases.',
    )
    parser.add_argument('--balanced',
        dest='balanced',
        type=str,
        required=True,
        help='Whether to do balanced or unbalanced workflow.',
    )
    parser.add_argument('--save-graphml',
        dest='save_graphml',
        type=str,
        required=True,
        help=''.join([
            'Whether to save GraphML graphical representation of diffusion distance ',
            'matrices. This may require a lot of disk space; approximately 200 GB for ',
            'a 500-image run with 10 channels. and a few thousand cells per image.'
        ])
    )
    parser.add_argument('--use-intensities',
        dest='use_intensities',
        type=str,
        required=True,
        help='Whether to involve intensity information for weighting.',
    )
    parser.add_argument('--dichotomize',
        dest='dichotomize',
        type=str,
        required=True,
        help='Whether to do dichotomization of continuous variables.',
    )
    parser.add_argument('--compartments',
        dest='compartments',
        type=str,
        required=True,
        help='Compartment names, comma separated.',
    )
    args = parser.parse_args()

    computational_workflow = re.sub(r'\\ ', ' ', args.computational_workflow)
    if computational_workflow in workflows:
        workflow = computational_workflow
    else:
        logger.error('Must select --computational-workflow from among: %s', list(workflows.keys()))
        return None

    job_working_directory = getcwd()
    sif_file = args.sif_file
    input_path = args.input_path
    outcomes_file = args.outcomes_file
    output_path = args.output_path
    jobs_path = args.jobs_path
    logs_path = args.logs_path
    schedulers_path = args.schedulers_path
    file_manifest_file = args.file_manifest_file
    runtime_platform = args.runtime_platform
    elementary_phenotypes_file = args.elementary_phenotypes_file
    complex_phenotypes_file = args.complex_phenotypes_file
    excluded_hostname = args.excluded_hostname
    skip_integrity_check = True if args.skip_integrity_check == 'True' else False
    balanced = True if args.balanced == 'True' else False
    save_graphml = True if args.save_graphml == 'True' else False
    use_intensities = True if args.use_intensities == 'True' else False
    dichotomize = True if args.dichotomize == 'True' else False

    parameters = {
        'workflow' : workflow,
        'job_working_directory' : job_working_directory,
        'input_path' : input_path,
        'outcomes_file' : outcomes_file,
        'output_path' : output_path,
        'jobs_path' : jobs_path,
        'logs_path' : logs_path,
        'schedulers_path' : schedulers_path,
        'sif_file' : sif_file,
        'file_manifest_file' : file_manifest_file,
        'runtime_platform' : runtime_platform,
        'elementary_phenotypes_file' : elementary_phenotypes_file,
        'complex_phenotypes_file' : complex_phenotypes_file,
        'excluded_hostname' : excluded_hostname,
    }
    if skip_integrity_check:
        parameters['skip_integrity_check'] = True
    if balanced:
        parameters['balanced'] = True
    if save_graphml:
        parameters['save_graphml'] = True
    if use_intensities:
        parameters['use_intensities'] = True
    if dichotomize:
        parameters['dichotomize'] = True

    compartments = args.compartments
    if compartments != '':
        compartments_list = [c.strip(' ') for c in compartments.split(',')]
        parameters['compartments'] = compartments_list
    return parameters

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
                'json_string. Try spt-configure.'
            ]),
            config_filename
        )
        return None

    if has_config_file:
        json_string = open(config_filename, 'rt').read()

    return json.loads(json_string)
