#!/usr/bin/env python3
"""
This script locates configuration parameters for the pipeline's job generation,
then delegates the job generation to a more specific generator.

It is not intended to be run directly by the user, as indicated by the
presence of the .py extension.
"""
import os
import sys
import argparse
import re
import configparser

import pandas as pd

import spatial_analysis_toolbox
from spatial_analysis_toolbox.api import get_job_generator
from spatial_analysis_toolbox.environment.configuration import workflows, config_filename  # use __init__.py system to expose these through api
from spatial_analysis_toolbox.environment.log_formats import colorized_logger

def get_config_parameters_from_cli():
    parser = argparse.ArgumentParser(
        description = ''.join([
            'This script generates jobs to be run optionally on an HPC (High-Performance Computing)',
            ' cluster using IBM\'s Platform LSF (Load Sharing Facility), and the commands to',
            ' schedule them or run them locally. The jobs do calculations with histology images.',
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
    args = parser.parse_args()

    computational_workflow = re.sub(r'\\ ', ' ', args.computational_workflow)
    if computational_workflow in workflows:
        workflow = computational_workflow
    else:
        logger.error('Must select --computational-workflow from among: %s', list(workflows.keys()))
        exit()

    job_working_directory = os.getcwd()
    sif_file = args.sif_file
    input_path = args.input_path
    outcomes_file = args.outcomes_file
    output_path = args.output_path
    jobs_path = args.jobs_path
    schedulers_path = args.schedulers_path
    file_manifest_file = args.file_manifest_file
    runtime_platform = args.runtime_platform
    elementary_phenotypes_file = args.elementary_phenotypes_file
    complex_phenotypes_file = args.complex_phenotypes_file

    parameters = {
        'workflow' : workflow,
        'job_working_directory' : job_working_directory,
        'input_path' : input_path,
        'outcomes_file' : outcomes_file,
        'output_path' : output_path,
        'jobs_path' : jobs_path,
        'schedulers_path' : schedulers_path,
        'sif_file' : sif_file,
        'file_manifest_file' : file_manifest_file,
        'runtime_platform' : runtime_platform,
        'elementary_phenotypes_file' : elementary_phenotypes_file,
        'complex_phenotypes_file' : complex_phenotypes_file,
    }
    return parameters

def get_config_parameters_from_file(config_filename):
    config = configparser.ConfigParser()
    config.read(config_filename)
    parameters = dict(config['default'])
    return parameters

def get_config_parameters():
    if len(sys.argv) == 1:
        if not os.path.exists(config_filename):
            logger.error('Configuration file %s does not exist.', config_filename)
            exit()
        else:
            return get_config_parameters_from_file(config_filename)
    else:
        parameters = get_config_parameters_from_cli()
        config = configparser.ConfigParser()
        config['default'] = parameters
        with open(config_filename, 'w') as file:
            config.write(file)
        return parameters

if __name__=='__main__':
    logger = colorized_logger(__name__)
    p = get_config_parameters()
    g = get_job_generator(**p)
    g.generate()
