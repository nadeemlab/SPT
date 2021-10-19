"""
Provides workflow definitions in terms of implementation classes, and
configuration parameter management.
"""
import importlib.resources
import sys
import argparse
import configparser
import os
from os import getcwd
from os.path import exists, abspath
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
                'json_string. Try spt-configure.'
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
            logger.warning(
                'Version mentioned in configuration file is %s, but running version of SPT is %s.',
                parameters[version_specifier],
                get_version(),
            )

    return parameters

def create_output_directories():
    dirs = {}

    output_path='output/'
    if not exists(output_path):
        os.mkdir(output_path)
    dirs['output_path'] = abspath(output_path)

    jobs_path='jobs/'
    if not exists(jobs_path):
        os.mkdir(jobs_path)
    dirs['jobs_path'] = abspath(jobs_path)

    logs_path='logs/'
    if not exists(logs_path):
        os.mkdir(logs_path)
    dirs['logs_path'] = abspath(logs_path)

    return dirs

def get_input_filenames_by_data_type(
    dataset_settings=None,
    file_metadata=None,
    data_type: str=None,
):
    """
    Retrieves from the file metadata table the names of all files with the given
    "Data type" field.

    :param dataset_settings: Wrapper around some input data settings (e.g. paths).
    :type dataset_settings: DatasetSettings

    :param file_metadata: The table of files.
    :type file_metadata: pd.DataFrame

    :param data_type: The file type descriptor.
    :type data_type: str

    :return: The list of filenames.
    :rtype: list
    """
    intact_files = []
    records = file_metadata[file_metadata['Data type'] == data_type]
    for i, row in records.iterrows():
        if row['Checksum scheme'] != 'SHA256':
            logger.error('Checksum scheme should be SHA256.')
            return

        expected_sha256 = row['Checksum']
        input_file_identifier = row['File ID']
        input_file = row['File name']
        input_file = abspath(join(dataset_settings.input_path, input_file))

        buffer_size = 65536
        sha = hashlib.sha256()
        with open(input_file, 'rb') as f:
            while True:
                data = f.read(buffer_size)
                if not data:
                    break
                sha.update(data)
        sha256 = sha.hexdigest()

        if sha256 != expected_sha256:
            logger.error(
                'File "%s" has wrong SHA256 hash (%s ; expected %s).',
                input_file_identifier,
                sha256,
                expected_sha256,
            )
            continue
        intact_files.append(input_file)
    return intact_files

def get_input_filename_by_identifier(
    dataset_settings=None,
    file_metadata=None,
    input_file_identifier: str=None,
):
    """
    Uses the file identifier to lookup the name of the associated file in the file
    metadata table, and cache the name of the associated file.

    :param dataset_settings: Wrapper around some input data settings (e.g. paths).
    :type dataset_settings: DatasetSettings

    :param file_metadata: The table of files.
    :type file_metadata: pd.DataFrame

    :param input_file_identifier: Key to search for in the "File ID" column of the
        file metadata table.
    :type input_file_identifier: str

    :return: The filename.
    :rtype: str
    """
    intact_files = []
    records = file_metadata[file_metadata['File ID'] == input_file_identifier]
    for i, row in records.iterrows():
        if row['Checksum scheme'] != 'SHA256':
            logger.error('Checksum scheme should be SHA256.')
            return

        expected_sha256 = row['Checksum']
        input_file_identifier = row['File ID']
        input_file = row['File name']
        input_file = abspath(join(dataset_settings.input_path, input_file))

        buffer_size = 65536
        sha = hashlib.sha256()
        with open(input_file, 'rb') as f:
            while True:
                data = f.read(buffer_size)
                if not data:
                    break
                sha.update(data)
        sha256 = sha.hexdigest()

        if sha256 != expected_sha256:
            logger.error(
                'File "%s" has wrong SHA256 hash (%s ; expected %s).',
                input_file_identifier,
                sha256,
                expected_sha256,
            )
            continue
        intact_files.append(input_file)
    if len(intact_files) > 0:
        logger.error('File identifier "%s" duplicated.', input_file_identifier)
    if len(intact_files) == 0:
        logger.error('File identifier "%s" not found.', input_file_identifier)
    return intact_files[0]
