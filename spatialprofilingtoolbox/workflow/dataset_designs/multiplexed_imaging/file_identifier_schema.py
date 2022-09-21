
import pandas as pd

from ....standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)

elementary_phenotypes_file_identifier = 'Elementary phenotypes file'
composite_phenotypes_file_identifier = 'Complex phenotypes file'
compartments_file_identifier = 'Compartments file'
default_file_manifest_filename = 'file_manifest.tsv'

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
