import os
from os import mkdir
from os.path import exists
from os.path import abspath
from os.path import join
import hashlib
from itertools import takewhile
from itertools import repeat

import pandas as pd

from ...log_formats import colorized_logger
logger = colorized_logger(__name__)


def raw_line_count(filename):
    file = open(filename, 'rb')
    buffer_generator = takewhile(
        lambda x: x,
        (file.raw.read(1024*1024) for _ in repeat(None)),
    )
    return sum( buffer.count(b'\n') for buffer in buffer_generator )

def compute_sha256(input_file):
    buffer_size = 65536
    sha = hashlib.sha256()
    with open(input_file, 'rb') as f:
        while True:
            data = f.read(buffer_size)
            if not data:
                break
            sha.update(data)
    return sha.hexdigest()

def get_input_filenames_by_data_type(
    data_type: str=None,
    file_manifest_filename: str=None,
):
    """
    Retrieves from the file metadata table the names of all files with the given
    "Data type" field.

    :param data_type: The file type descriptor.
    :type data_type: str

    :return: The list of filenames.
    :rtype: list
    """
    if file_manifest_filename is None:
        raise ValueError('Need to supply file_manifest_filename.')
    file_metadata = pd.read_csv(file_manifest_filename, sep='\t')
    records = file_metadata[file_metadata['Data type'] == data_type]
    return list(records['File name'])

def get_input_filename_by_identifier(
    input_file_identifier: str=None,
    file_manifest_filename: str=None,
):
    """
    Uses the file identifier to lookup the name of the associated file in the file
    metadata table, and cache the name of the associated file.

    :param file_metadata: The table of files.
    :type file_metadata: pd.DataFrame

    :param input_file_identifier: Key to search for in the "File ID" column of the
        file metadata table.
    :type input_file_identifier: str

    :return: The filename.
    :rtype: str
    """
    if file_manifest_filename is None:
        raise ValueError('Need to supply file_manifest_filename.')
    file_metadata = pd.read_csv(file_manifest_filename, sep='\t')
    records = file_metadata[file_metadata['File ID'] == input_file_identifier]
    filenames = list(records['File name'])
    if len(filenames) > 1:
        logger.warning('File identifier "%s" duplicated.', input_file_identifier)
        return None
    if len(filenames) == 0:
        logger.warning('File identifier "%s" not found.', input_file_identifier)
        return None
    return filenames[0]
