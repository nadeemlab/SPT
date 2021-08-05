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

from ..dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign
from ..workflows.diffusion.job_generator import DiffusionJobGenerator
from ..workflows.diffusion.computational_design import DiffusionDesign
from ..workflows.diffusion.analyzer import DiffusionAnalyzer
from ..workflows.diffusion.integrator import DiffusionAnalysisIntegrator
from ..workflows.phenotype_proximity.job_generator import PhenotypeProximityJobGenerator
from ..workflows.phenotype_proximity.computational_design import PhenotypeProximityDesign
from ..workflows.phenotype_proximity.analyzer import PhenotypeProximityAnalyzer
from ..workflows.phenotype_proximity.integrator import PhenotypeProximityAnalysisIntegrator
from ..workflows.front_proximity.job_generator import FrontProximityJobGenerator
from ..workflows.front_proximity.computational_design import FrontProximityDesign
from ..workflows.front_proximity.analyzer import FrontProximityAnalyzer
from ..workflows.front_proximity.integrator import FrontProximityAnalysisIntegrator
from ..workflows.frequency.job_generator import FrequencyJobGenerator
from ..workflows.frequency.computational_design import FrequencyDesign
from ..workflows.frequency.analyzer import FrequencyAnalyzer
from ..workflows.frequency.integrator import FrequencyAnalysisIntegrator
# Migrate above imports down to workflow modules

config_filename = '.spt_pipeline.config'


class WorkflowModules:
    """
    A wrapper object in which to list implementation classes comprising a workflow definition.
    """
    def __init__(self, generator=None, dataset_design=None, computational_design=None, analyzer=None, integrator=None):
        self.generator = generator
        self.dataset_design = dataset_design
        self.computational_design = computational_design
        self.analyzer = analyzer
        self.integrator = integrator

workflows = {
    'Multiplexed IF diffusion' : WorkflowModules(
        generator = DiffusionJobGenerator,
        dataset_design = HALOCellMetadataDesign,
        computational_design = DiffusionDesign,
        analyzer = DiffusionAnalyzer,
        integrator = DiffusionAnalysisIntegrator,
    ),
    'Multiplexed IF phenotype proximity' : WorkflowModules(
        generator = PhenotypeProximityJobGenerator,
        dataset_design = HALOCellMetadataDesign,
        computational_design = PhenotypeProximityDesign,
        analyzer = PhenotypeProximityAnalyzer,
        integrator = PhenotypeProximityAnalysisIntegrator,
    ),
    'Multiplexed IF front proximity' : WorkflowModules(
        generator = FrontProximityJobGenerator,
        dataset_design = HALOCellMetadataDesign,
        computational_design = FrontProximityDesign,
        analyzer = FrontProximityAnalyzer,
        integrator = FrontProximityAnalysisIntegrator,
    ),
    'Multiplexed IF frequency' : WorkflowModules(
        generator = FrequencyJobGenerator,
        dataset_design = HALOCellMetadataDesign,
        computational_design = FrequencyDesign,
        analyzer = FrequencyAnalyzer,
        integrator = FrequencyAnalysisIntegrator,
    ),
}

def get_config_parameters_from_file():
    """
    Retrieves previously-serialized configuration parameters from file, using a
    singleton pattern.

    Returns:
        dict:
            Key-value pairs parsed using the Python standard library configparser
            module.
    """
    config = configparser.ConfigParser()
    config.read(config_filename)
    parameters = dict(config['default'])
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
    schedulers_path = args.schedulers_path
    file_manifest_file = args.file_manifest_file
    runtime_platform = args.runtime_platform
    elementary_phenotypes_file = args.elementary_phenotypes_file
    complex_phenotypes_file = args.complex_phenotypes_file
    excluded_hostname = args.excluded_hostname
    skip_integrity_check = True if args.skip_integrity_check == 'True' else False

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
        'excluded_hostname' : excluded_hostname,
    }
    if skip_integrity_check:
        parameters['skip_integrity_check'] = True
    return parameters

def get_config_parameters():
    if len(sys.argv) == 1:
        if not exists(config_filename):
            logger.error('Configuration file %s does not exist.', config_filename)
            return None
        else:
            return get_config_parameters_from_file()
    else:
        parameters = get_config_parameters_from_cli()
        write_config_parameters_to_file(parameters)
        return parameters
