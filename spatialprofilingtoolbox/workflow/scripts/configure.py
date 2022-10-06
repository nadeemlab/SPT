import argparse
from shutil import which
import os
from os import getcwd
import stat
from os.path import isdir
from os.path import exists
from os.path import join
from os.path import abspath
from os.path import expanduser
from os import getcwd
import importlib.resources

import spatialprofilingtoolbox
from spatialprofilingtoolbox import get_workflow
from spatialprofilingtoolbox import get_workflow_names
workflows = {name : get_workflow(name) for name in get_workflow_names()}

nf_config_file = 'nextflow.config'
nf_pipeline_file = 'main.nf'


def retrieve_from_library(subpackage, filename):
    contents = None
    with importlib.resources.path('.'.join(['spatialprofilingtoolbox', subpackage]), filename) as path:
        with open(path, 'rt') as file:
            contents = file.read()
    if contents is None:
        raise Exception('Could not locate library file %s' % filename)
    return contents

def write_config_file(variables):
    contents = retrieve_from_library('workflow.templates', nf_config_file + '.jinja')
    template = jinja_environment.from_string(contents)
    config_file = template.render(**variables)
    with open(join(getcwd(), nf_config_file), 'wt') as file:
        file.write(config_file)

def write_pipeline_script(variables):
    contents = retrieve_from_library('workflow.templates', nf_pipeline_file + '.jinja')
    template = jinja_environment.from_string(contents)
    pipeline_file = template.render(**variables)
    with open(join(os.getcwd(), nf_pipeline_file), 'wt') as file:
        file.write(pipeline_file)

def record_configuration_command(variables):
    tokens = ['spt workflow configure']
    tokens.append('--workflow="%s"' % variables['workflow'])
    if variables['executor'] == 'local':
        tokens.append('--local')
    if variables['executor'] == 'lsf':
        tokens.append('--lsf')
    input_path = abspath(variables['input_path'])
    if ' ' in input_path:
        input_path = "'%s'" % input_path
    tokens.append('--input-path=%s' % input_path)
    if 'sif_file' in variables:
        sif_file = abspath(variables['sif_file'])
        if ' ' in sif_file:
            sif_file = "'%s'" % sif_file
        tokens.append('--sif-file=%s' % sif_file)
    if 'excluded_host' in variables:
        tokens.append('--excluded-host=%s' % variables['excluded_host'])
    if 'db_config_file' in variables:
        tokens.append('--database-config-file=%s' % variables['db_config_file'])

    command = ' \\\n '.join(tokens)

    with open('configure.sh', 'wt') as file:
        file.write('#!/bin/sh\n\n')
        file.write(command)
        file.write('\n')

    with open('run.sh', 'wt') as file:
        file.write('#!/bin/sh\n\n')
        file.write('nextflow run .\n')

    st = os.stat('configure.sh')
    os.chmod('configure.sh', st.st_mode | stat.S_IEXEC)
    st = os.stat('run.sh')
    os.chmod('run.sh', st.st_mode | stat.S_IEXEC)

if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog = 'spt workflow configure',
        description = 'Configure an SPT (spatialprofilingtoolbox) run in the current directory.'
    )
    parser.add_argument(
        '--workflow',
        choices=get_workflow_names(),
        required=True,
    )
    parser.add_argument(
        '--input-path',
        dest='input_path',
        type=str,
        required=True,
        help='Path to directory containing input data files. (For example, containing file_manifest.tsv).',
    )
    parser.add_argument(
        '--sif-file',
        dest='sif_file',
        type=str,
        required=False,
        help='Path to SPT Singularity container. Can be obtained with singularity pull docker://nadeemlab/spt:latest',
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
        help='Use this flag to get Nextflow to attempt to deploy processes as Platform LSF jobs on an HPC cluster.',
    )
    parser.add_argument(
        '--excluded-host',
        dest='excluded_host',
        type=str,
        required=False,
        help='If a machine must not have LSF jobs scheduled on it, supply its hostname here.',
    )
    parser.add_argument(
        '--database-config-file',
        dest='database_config_file',
        type=str,
        required=False,
        help='If workflow involves database, provide the config file here.',
    )
    args = parser.parse_args()

    from spatialprofilingtoolbox.standalone_utilities.module_load_error import SuggestExtrasException
    try:
        import jinja2
        from spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.file_identifier_schema import default_file_manifest_filename
        from spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.file_identifier_schema import get_input_filename_by_identifier
        from spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.file_identifier_schema import get_input_filenames_by_data_type
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'workflow')

    jinja_environment = jinja2.Environment(loader=jinja2.BaseLoader)

    variables = {}

    if args.local:
        variables['executor'] = 'local'
    if args.lsf:
        variables['executor'] = 'lsf'

    variables['workflow'] = args.workflow

    if isdir(args.input_path):
        file_manifest_path = join(args.input_path, default_file_manifest_filename)
        if exists(file_manifest_path):
            variables['input_path'] = args.input_path
            variables['file_manifest_filename'] = file_manifest_path
        else:
            raise FileNotFoundError(file_manifest_path)
    else:
        raise FileNotFoundError(args.input_path)

    if not args.sif_file is None:
        if exists(args.sif_file):
            variables['sif_file'] = args.sif_file
        else:
            raise FileNotFoundError(args.sif_file)

    if not args.excluded_host is None:
        variables['excluded_host'] = args.excluded_host

    variables['current_working_directory'] = getcwd()

    compartments_file = get_input_filename_by_identifier(
        input_file_identifier = 'Compartments file',
        file_manifest_filename = file_manifest_path,
    )
    variables['compartments'] = False
    if not compartments_file is None:
        compartments_file_abs = join(args.input_path, compartments_file)
        if exists(compartments_file_abs):
            variables['compartments_file'] = compartments_file_abs
            variables['compartments'] = True

    outcomes_files = get_input_filenames_by_data_type(
        data_type = 'Outcome',
        file_manifest_filename = file_manifest_path,
    )
    variables['outcomes'] = False
    if len(outcomes_files) > 0:
        outcomes_file_abs = join(args.input_path, outcomes_files[0])
        if exists(outcomes_file_abs):
            variables['outcomes_file'] = outcomes_file_abs
            variables['outcomes'] = True

    if args.database_config_file:
        config_file = expanduser(args.database_config_file)
    if exists(config_file):
        if workflows[variables['workflow']].computational_design.uses_database():
            variables['db_config_file'] = config_file
            variables['db_config'] = True

    subjects_file = get_input_filename_by_identifier(
        input_file_identifier = 'Subjects file',
        file_manifest_filename = file_manifest_path,
    )
    variables['subjects'] = False
    if not subjects_file is None:
        subjects_file_abs = join(args.input_path, subjects_file)
        if exists(subjects_file_abs):
            variables['subjects_file'] = subjects_file_abs
            variables['subjects'] = True

    write_config_file(variables)
    write_pipeline_script(variables)
    record_configuration_command(variables)
