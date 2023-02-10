"""CLI utility to configure an SPT workflow run."""
import argparse
import os
from os import getcwd
from os.path import isdir
from os.path import exists
from os.path import join
from os.path import abspath
from os.path import expanduser
import stat
import importlib.resources

from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox import get_workflow
from spatialprofilingtoolbox import get_workflow_names

workflows = {name: get_workflow(name) for name in get_workflow_names()}

NF_CONFIG_FILE = 'nextflow.config'
NF_PIPELINE_FILE = 'main.nf'
NF_PIPELINE_FILE_VISITOR = 'main_visitor.nf'


def retrieve_from_library(subpackage, filename):
    contents = None
    with importlib.resources.path('.'.join(['spatialprofilingtoolbox', subpackage]),
                                  filename) as path:
        with open(path, 'rt', encoding='utf-8') as file:
            contents = file.read()
    if contents is None:
        raise FileNotFoundError(f'Could not locate library file {filename}')
    return contents


def write_config_file(variables):
    contents = retrieve_from_library('workflow.assets', NF_CONFIG_FILE + '.jinja')
    template = jinja_environment.from_string(contents)
    file_to_write = template.render(**variables)
    with open(join(getcwd(), NF_CONFIG_FILE), 'wt', encoding='utf-8') as file:
        file.write(file_to_write)


def write_pipeline_script(variables):
    if workflows[variables['workflow']].is_database_visitor:
        pipeline_file = retrieve_from_library('workflow.assets', NF_PIPELINE_FILE_VISITOR)
    else:
        pipeline_file = retrieve_from_library('workflow.assets', NF_PIPELINE_FILE)
    with open(join(os.getcwd(), NF_PIPELINE_FILE), 'wt', encoding='utf-8') as file:
        file.write(pipeline_file)


def record_configuration_command(variables):
    tokens = ['spt workflow configure']
    tokens.append(f"--workflow=\"{variables['workflow']}\"")
    if variables['executor'] == 'local':
        tokens.append('--local')
    if variables['executor'] == 'lsf':
        tokens.append('--lsf')
    if 'input_path' in variables:
        input_path = abspath(variables['input_path'])
        if ' ' in input_path:
            input_path = f"'{input_path}'"
        tokens.append(f'--input-path={input_path}')
    if 'sif_file' in variables:
        sif_file = abspath(variables['sif_file'])
        if ' ' in sif_file:
            sif_file = f"'{sif_file}'"
        tokens.append(f'--sif-file={sif_file}')
    if 'excluded_host' in variables:
        tokens.append(f'--excluded-host={variables["excluded_host"]}')
    if 'db_config_file' in variables:
        tokens.append(f'--database-config-file={variables["db_config_file"]}')

    command = ' \\\n '.join(tokens)

    with open('configure.sh', 'wt', encoding='utf-8') as file:
        file.write('#!/bin/sh\n\n')
        file.write(command)
        file.write('\n')

    with open('run.sh', 'wt', encoding='utf-8') as file:
        file.write('#!/bin/sh\n\n')
        file.write('nextflow run .\n')

    file_stat = os.stat('configure.sh')
    os.chmod('configure.sh', file_stat.st_mode | stat.S_IEXEC)
    file_stat = os.stat('run.sh')
    os.chmod('run.sh', file_stat.st_mode | stat.S_IEXEC)


def process_filename_inputs(options, parsed_args):
    if isdir(parsed_args.input_path):
        file_manifest_path = join(parsed_args.input_path, 'file_manifest.tsv')
        if exists(file_manifest_path):
            options['input_path'] = parsed_args.input_path
            options['file_manifest_filename'] = file_manifest_path
        else:
            raise FileNotFoundError(file_manifest_path)
    else:
        raise FileNotFoundError(parsed_args.input_path)

    samples_file = get_input_filename_by_identifier(
        input_file_identifier='Samples file',
        file_manifest_filename=file_manifest_path,
    )
    options['samples'] = False
    if not samples_file is None > 0:
        samples_file_abs = join(parsed_args.input_path, samples_file)
        if exists(samples_file_abs):
            options['samples_file'] = samples_file_abs
            options['samples'] = True

    subjects_file = get_input_filename_by_identifier(
        input_file_identifier='Subjects file',
        file_manifest_filename=file_manifest_path,
    )
    options['subjects'] = False
    if not subjects_file is None:
        subjects_file_abs = join(parsed_args.input_path, subjects_file)
        if exists(subjects_file_abs):
            options['subjects_file'] = subjects_file_abs
            options['subjects'] = True

    study_file = get_input_filename_by_identifier(
        input_file_identifier='Study file',
        file_manifest_filename=file_manifest_path,
    )
    study_file_abs = join(parsed_args.input_path, study_file)
    if not exists(study_file_abs):
        raise FileNotFoundError(f'Did not find study file ({study_file}).')
    options['study_file'] = study_file_abs
    options['study'] = True

    diagnosis_file = get_input_filename_by_identifier(
        input_file_identifier='Diagnosis file',
        file_manifest_filename=file_manifest_path,
    )
    diagnosis_file_abs = join(parsed_args.input_path, diagnosis_file)
    if not exists(diagnosis_file_abs):
        raise FileNotFoundError(f'Did not find diagnosis file ({diagnosis_file}).')
    options['diagnosis_file'] = diagnosis_file_abs
    options['diagnosis'] = True

    interventions_file = get_input_filename_by_identifier(
        input_file_identifier='Interventions file',
        file_manifest_filename=file_manifest_path,
    )
    interventions_file_abs = join(parsed_args.input_path, interventions_file)
    if not exists(interventions_file_abs):
        raise FileNotFoundError(f'Did not find interventions file ({interventions_file}).')
    options['interventions_file'] = interventions_file_abs
    options['interventions'] = True

    channels_file = get_input_filename_by_identifier(
        input_file_identifier='Channels file',
        file_manifest_filename=file_manifest_path,
    )
    channels_file_abs = join(parsed_args.input_path, channels_file)
    if not exists(channels_file_abs):
        raise FileNotFoundError(f'Did not find channels file ({channels_file}).')
    options['channels_file'] = channels_file_abs
    options['channels'] = True

    phenotypes_file = get_input_filename_by_identifier(
        input_file_identifier='Phenotypes file',
        file_manifest_filename=file_manifest_path,
    )
    phenotypes_file_abs = join(parsed_args.input_path, phenotypes_file)
    if not exists(phenotypes_file_abs):
        raise FileNotFoundError(f'Did not find phenotypes file ({phenotypes_file}).')
    options['phenotypes_file'] = phenotypes_file_abs
    options['phenotypes'] = True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt workflow configure',
        description='Configure an SPT (spatialprofilingtoolbox) run in the current directory.'
    )
    add_argument(parser, 'workflow')
    add_argument(parser, 'study name')
    parser.add_argument(
        '--input-path',
        dest='input_path',
        type=str,
        required=False,
        help='Path to directory containing input data files. (For example, containing '
        'file_manifest.tsv).'
    )
    parser.add_argument(
        '--sif-file',
        dest='sif_file',
        type=str,
        required=False,
        help='Path to SPT Singularity container. Can be obtained with singularity pull '
        'docker://nadeemlab/spt:latest'
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--local',
        action='store_true',
        default=False,
        help='Use this flag to get Nextflow to deploy processes locally on a given machine.'
    )
    group.add_argument(
        '--lsf',
        action='store_true',
        default=False,
        help='Use this flag to get Nextflow to attempt to deploy processes as Platform LSF jobs on'
        ' an HPC cluster.'
    )
    parser.add_argument(
        '--excluded-host',
        dest='excluded_host',
        type=str,
        required=False,
        help='If a machine must not have LSF jobs scheduled on it, supply its hostname here.'
    )
    add_argument(parser, 'database config')
    args = parser.parse_args()

    from spatialprofilingtoolbox.standalone_utilities.module_load_error import \
        SuggestExtrasException
    try:
        import jinja2
        from spatialprofilingtoolbox.workflow.common.\
            file_identifier_schema import get_input_filename_by_identifier # pylint: disable=ungrouped-imports
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'workflow')

    jinja_environment = jinja2.Environment(loader=jinja2.BaseLoader())

    config_variables = {}

    config_variables['workflow'] = args.workflow

    if args.database_config_file:
        config_file = expanduser(args.database_config_file)
        if exists(config_file):
            config_variables['db_config_file'] = config_file
            config_variables['db_config'] = True

    if args.local:
        config_variables['executor'] = 'local'
    if args.lsf:
        config_variables['executor'] = 'lsf'

    if args.study_name:
        config_variables['study_name'] = args.study_name

    if not args.sif_file is None:
        if exists(args.sif_file):
            config_variables['sif_file'] = args.sif_file
        else:
            raise FileNotFoundError(args.sif_file)

    if not args.excluded_host is None:
        config_variables['excluded_host'] = args.excluded_host

    config_variables['current_working_directory'] = getcwd()

    if not workflows[config_variables['workflow']].is_database_visitor:
        process_filename_inputs(config_variables, args)

    write_config_file(config_variables)
    write_pipeline_script(config_variables)
    record_configuration_command(config_variables)
