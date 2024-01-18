"""CLI utility to configure an SPT workflow run."""

import re
from argparse import ArgumentParser
from os import (
    getcwd,
    stat,
    chmod,
)
from os.path import (
    isdir,
    exists,
    join,
    abspath,
    expanduser,
)
from stat import S_IEXEC
from configparser import ConfigParser
from importlib.resources import as_file
from importlib.resources import files
from typing import cast

try:
    from jinja2 import Environment, BaseLoader
except ModuleNotFoundError as e:
    from spatialprofilingtoolbox.standalone_utilities.module_load_error import \
        SuggestExtrasException
    SuggestExtrasException(e, 'workflow')
from jinja2 import Environment, BaseLoader  # pylint: disable=ungrouped-imports

from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument  # pylint: disable=ungrouped-imports
from spatialprofilingtoolbox import get_workflow
from spatialprofilingtoolbox import get_workflow_names
from spatialprofilingtoolbox.workflow.common.\
    file_identifier_schema import get_input_filename_by_identifier

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt db configure')

workflows = {name: get_workflow(name) for name in get_workflow_names()}

NF_CONFIG_FILE = 'nextflow.config'
NF_PIPELINE_FILE = 'main.nf'
NF_PIPELINE_FILE_VISITOR = 'main_visitor.nf'
NF_PIPELINE_FILE_CGGNN = 'cggnn.nf'


def _retrieve_from_library(subpackage: str, filename: str) -> str:
    filepath = files('.'.join(['spatialprofilingtoolbox', subpackage])).joinpath(filename)
    with as_file(filepath) as path:
        with open(path, 'rt', encoding='utf-8') as file:
            contents = file.read()
    return contents


def _write_config_file(variables: dict[str, str]) -> None:
    contents = _retrieve_from_library('workflow.assets', NF_CONFIG_FILE + '.jinja')
    template = jinja_environment.from_string(contents)
    file_to_write = template.render(**variables)
    file_to_write = re.sub(r'\n\n+', '\n', file_to_write)
    with open(join(getcwd(), NF_CONFIG_FILE), 'wt', encoding='utf-8') as file:
        file.write(file_to_write)


def _write_pipeline_script(variables: dict[str, str]) -> None:
    workflow_name = variables['workflow']
    if workflows[workflow_name].is_database_visitor:
        if workflow_name == 'cg-gnn':
            pipeline_file = _retrieve_from_library('workflow.assets', NF_PIPELINE_FILE_CGGNN)
        else:
            pipeline_file = _retrieve_from_library('workflow.assets', NF_PIPELINE_FILE_VISITOR)
    else:
        pipeline_file = _retrieve_from_library('workflow.assets', NF_PIPELINE_FILE)
    with open(join(getcwd(), NF_PIPELINE_FILE), 'wt', encoding='utf-8') as file:
        file.write(pipeline_file)


def _record_configuration_command(variables: dict[str, str], configuration_file: str) -> None:
    tokens = ['spt workflow configure']
    tokens.append(f"--workflow=\"{variables['workflow']}\"")
    configuration_file = abspath(configuration_file)
    if ' ' in configuration_file:
        configuration_file = f'"{configuration_file}"'
    tokens.append(f"--config-file=\"{configuration_file}\"")
    command = ' \\\n '.join(tokens)

    with open('configure.sh', 'wt', encoding='utf-8') as file:
        file.write('#!/bin/sh\n\n')
        file.write(command)
        file.write('\n')

    with open('run.sh', 'wt', encoding='utf-8') as file:
        file.write('#!/bin/sh\n\n')
        file.write('nextflow run .\n')

    file_stat = stat('configure.sh')
    chmod('configure.sh', file_stat.st_mode | S_IEXEC)
    file_stat = stat('run.sh')
    chmod('run.sh', file_stat.st_mode | S_IEXEC)


def _process_filename_inputs(options: dict[str, str | bool]) -> None:
    if not 'input_path' in options:
        return
    input_path = cast(str, options['input_path'])
    del options['input_path']
    if isdir(input_path):
        file_manifest_path = join(input_path, 'file_manifest.tsv')
        if exists(file_manifest_path):
            options['input_path'] = input_path
            options['file_manifest_filename'] = file_manifest_path
        else:
            raise FileNotFoundError(file_manifest_path)
    else:
        raise FileNotFoundError(input_path)

    samples_file = get_input_filename_by_identifier(
        input_file_identifier='Samples file',
        file_manifest_filename=file_manifest_path,
    )
    options['samples'] = False
    if not samples_file is None:
        samples_file_abs = join(input_path, samples_file)
        if exists(samples_file_abs):
            options['samples_file'] = samples_file_abs
            options['samples'] = True

    subjects_file = get_input_filename_by_identifier(
        input_file_identifier='Subjects file',
        file_manifest_filename=file_manifest_path,
    )
    options['subjects'] = False
    if not subjects_file is None:
        subjects_file_abs = join(input_path, subjects_file)
        if exists(subjects_file_abs):
            options['subjects_file'] = subjects_file_abs
            options['subjects'] = True

    study_file = get_input_filename_by_identifier(
        input_file_identifier='Study file',
        file_manifest_filename=file_manifest_path,
    )
    if not study_file is None:
        study_file_abs = join(input_path, study_file)
        if not exists(study_file_abs):
            raise FileNotFoundError(f'Did not find study file ({study_file}).')
        options['study_file'] = study_file_abs
        options['study'] = True

    diagnosis_file = get_input_filename_by_identifier(
        input_file_identifier='Diagnosis file',
        file_manifest_filename=file_manifest_path,
    )
    if not diagnosis_file is None:
        diagnosis_file_abs = join(input_path, diagnosis_file)
        if not exists(diagnosis_file_abs):
            raise FileNotFoundError(f'Did not find diagnosis file ({diagnosis_file}).')
        options['diagnosis_file'] = diagnosis_file_abs
        options['diagnosis'] = True

    interventions_file = get_input_filename_by_identifier(
        input_file_identifier='Interventions file',
        file_manifest_filename=file_manifest_path,
    )
    if not interventions_file is None:
        interventions_file_abs = join(input_path, interventions_file)
        if not exists(interventions_file_abs):
            raise FileNotFoundError(f'Did not find interventions file ({interventions_file}).')
        options['interventions_file'] = interventions_file_abs
        options['interventions'] = True

    channels_file = get_input_filename_by_identifier(
        input_file_identifier='Channels file',
        file_manifest_filename=file_manifest_path,
    )
    if not channels_file is None:
        channels_file_abs = join(input_path, channels_file)
        if not exists(channels_file_abs):
            raise FileNotFoundError(f'Did not find channels file ({channels_file}).')
        options['channels_file'] = channels_file_abs
        options['channels'] = True

    phenotypes_file = get_input_filename_by_identifier(
        input_file_identifier='Phenotypes file',
        file_manifest_filename=file_manifest_path,
    )
    if not phenotypes_file is None:
        phenotypes_file_abs = join(input_path, phenotypes_file)
        if not exists(phenotypes_file_abs):
            raise FileNotFoundError(f'Did not find phenotypes file ({phenotypes_file}).')
        options['phenotypes_file'] = phenotypes_file_abs
        options['phenotypes'] = True


def parse_arguments():
    """Process command line arguments."""
    parser = ArgumentParser(
        prog='spt workflow configure',
        description="""Configure an SPT (spatialprofilingtoolbox) run in the current directory.

Below the format of the workflow configuration file is described.

General variables should be included under:
`[general]`:
    db_config_file: <path>
        Path to a database configuration file.
    executor: {local, lsf} (default: local)
        Determines if processes are run locally or as Platform LSF jobs on an HPC cluster.
    excluded_host: <hostname> (default: None)
        If specified, LSF jobs will not be scheduled on the indicated host.
    sif-file: <path> (default: None)
        Path to SPT Singularity container. Can be obtained with singularity pull
        docker://nadeemlab/spt:latest

Some workflows require additional variables that are defined in their own section.

`[tabular_import]`:
    input_path: <path>
        Path to the directory containing the input data files, e.g., `file_manifest.tsv`.

`[cg-gnn]`:
    default_docker_image: <docker image name>
        Name of the Docker image to use for the CG-GNN workflow (outside of the training step, which
        uses a specific container).
    network:
        Name of the Docker network to use for the CG-GNN workflow.
    graph_config_file: <path>
        Path to the graph configuration file. See spatialprofilingtoolbox.cggnn for more details.
    cuda: {true, false} (default: false)
        Whether to use a CUDA-enabled container for the CG-GNN workflow training step.
    upload_importances: {true, false} (default: false)
        Whether to upload feature importances to the database after training.
"""
    )
    add_argument(parser, 'workflow')
    parser.add_argument(
        '--config-file',
        help='Path to a workflow configuration file. This file will be used to populate the '
        'configuration file for the workflow.',
        required=True,
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    jinja_environment = Environment(loader=BaseLoader())

    config_variables: dict[str, str | bool] = {}
    config_file = ConfigParser()
    config_file.read(args.config_file)
    config_variables = dict(config_file.items('general')) if config_file.has_section('general') \
        else {}
    workflow: str = args.workflow
    workflow_configuration = workflows[workflow]
    config_variables['workflow'] = args.workflow

    if 'db_config_file' not in config_variables:
        raise ValueError('db_config_file must be specified in the workflow configuration file.')
    db_config_file = expanduser(cast(str, config_variables['db_config_file']))
    if exists(db_config_file):
        config_variables['db_config_file'] = db_config_file
        config_variables['db_config'] = True
    else:
        logger.warning('Database configuration file was not found at the indicated location.')
        logger.debug('database_config_file: %s', config_variables['db_config_file'])
        logger.debug('db_config_file: %s', db_config_file)

    if 'executor' not in config_variables:
        config_variables['executor'] = 'local'
    if config_variables['executor'] not in {'local', 'lsf'}:
        raise ValueError('executor must be either "local" or "lsf". '
                         f'Got {config_variables["executor"]}')
    if 'excluded_host' in config_variables:
        if cast(str, config_variables['excluded_host']).lower().strip() == 'none':
            del config_variables['excluded_host']
    if ('excluded_host' in config_variables) and (config_variables['executor'] == 'local'):
        logger.warning('excluded_host specified despite executor being "local".')
        del config_variables['excluded_host']

    if 'sif_file' in config_variables:
        if cast(str, config_variables['sif_file']).lower().strip() == 'none':
            del config_variables['sif_file']
        if not exists(config_variables['sif_file']):
            raise FileNotFoundError(config_variables['sif_file'])

    config_variables['current_working_directory'] = getcwd()

    if workflow_configuration.is_database_visitor:
        db_visitor_config = dict(config_file.items('database visitor'))
        if 'study_name' not in db_visitor_config:
            raise ValueError('study_name must be specified in the `database visitor` section.')
        config_variables.update(db_visitor_config)

    if config_file.has_section(workflow):
        config_section = dict(config_file.items(workflow))
        workflow_configuration.process_inputs(config_section)
        config_variables.update(config_section)
    elif workflow_configuration.config_section_required:
        raise ValueError(f'Workflow {workflow} requires a configuration section.')

    if not workflow_configuration.is_database_visitor:
        _process_filename_inputs(config_variables)

    _write_config_file(config_variables)
    _write_pipeline_script(config_variables)
    _record_configuration_command(config_variables, args.config_file)
    if workflow == 'phenotype proximity':
        print(config_variables)
