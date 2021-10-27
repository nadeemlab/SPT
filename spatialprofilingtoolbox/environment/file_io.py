import os
from os import mkdir
from os.path import exists, abspath, join
import hashlib
FIND_FILES_USING_PATH = ('FIND_FILES_USING_PATH' in os.environ)

import pandas as pd

from .log_formats import colorized_logger
logger = colorized_logger(__name__)


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
        if FIND_FILES_USING_PATH:
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
        if FIND_FILES_USING_PATH:
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
    if len(intact_files) > 1:
        logger.error('File identifier "%s" duplicated.', input_file_identifier)
        return None
    if len(intact_files) == 0:
        logger.error('File identifier "%s" not found.', input_file_identifier)
        return None
    return intact_files[0]

def get_outcomes_files(dataset_settings):
    outcomes_files = get_input_filenames_by_data_type(
        dataset_settings = dataset_settings,
        file_metadata = pd.read_csv(dataset_settings.file_manifest_file, sep='\t'),
        data_type = 'Outcome',
    )
    return outcomes_files
