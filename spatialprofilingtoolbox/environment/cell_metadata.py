import os
from os.path import exists

import pandas as pd

from .log_formats import colorized_logger

logger = colorized_logger(__name__)


class CellMetadata:
    """
    A source-agnostic interface for an object to wrap a large amount of cell
    metadata, including functionality to serialize to / retrieve from file, and to
    quickly query for cells in a given sample and field of view.
    """
    table_header_constant_portion = {
        'Sample ID index column name' : 'Sample ID index',
        'Field of view index column name' : 'Field of view index',
    }
    table_header_template = {
        'positivity column name' : '{{channel specifier}}+',
        'intensity column name' : '{{channel specifier}} intensity',
    }
    default_cache_location = '.cell_metadata.tsv.cache'

    def __init__(
            self,
            dataset_design=None,
            file_manifest_file: str=None,
            input_files_path: str=None,
            cache_location: str='.cell_metadata.tsv.cache',
        ):
        """
        :param dataset_design:
            Object providing get_elementary_phenotype_names, get_pandas_signature,
            get_combined_intensity, and get_box_limit_column_names.
        :type dataset_design:

        :param file_manifest_file: Path to the manifest of source files containing
            cell-level information.
        :type file_manifest_file: str

        :param input_file_path: The path to the directory containing the input files
            described the file manifest.
        :type input_file_path: str

        :param cache_location: (Optional) An alternative file location to cache the
            cell-related tables.
        :type cache_location: str
        """
        self.input_files_path = input_files_path
        self.dataset_design = dataset_design
        self.cache_location = cache_location
        self.file_manifest_file = file_manifest_file
        self.file_metadata = pd.read_csv(file_manifest_file, sep='\t')
        self.cells = pd.DataFrame()

    def initialize(self):
        """
        Pulls in cell metadata table from cache, or creates the cache if it does not yet
        exist.

        Typically this should be called right after ``__init__``.
        """
        self.cells = self.load_cache_file()

    def get_cell_info_table(self, input_files_path, file_metadata, dataset_design):
        """
        :param input_files_path: Path to directory containing input files described by
            the file manifest.
        :type input_files_path: str

        :param file_metadata: Table of file metadata.
        :type file_metadata: pandas.DataFrame

        :param dataset_design: Dataset design object.

        :return: The table of cell metadata. The format should be as described by
            :py:meth:`get_metadata`.
        :rtype: pandas.DataFrame
        """
        pass

    def get_sample_id_index(self, sample_id):
        """
        :param sample_id: A sample identifier.
        :type sample_id: str

        :return: The integer index of the sample identifier.
        :rtype: int
        """
        pass

    def get_fov_index(self, sample_id, fov):
        """
        :param sample_id: A sample identifier.
        :type sample_id: str

        :param fov: A field of view identifier string.
        :type fov: str

        :return: The integer index of the field of view in the given sample.
        :rtype: int
        """
        pass

    def get_cells_table(self):
        return self.cells

    def load_cache_file(self):
        """
        If not yet cached, creates table of cells from source files listed in the given
        file manifest, then caches this to file.

        Otherwise, loads directly from the cache file.

        :return: The table of cell metadata. The format should be as described by
            :py:meth:`get_metadata`.
        :rtype: pandas.DataFrame
        """
        if not exists(self.cache_location):
            logger.info('Gathering cell info from files listed in %s', self.file_manifest_file)
            table = self.get_cell_info_table(
                self.input_files_path,
                self.file_metadata,
                self.dataset_design,
            )
            logger.info('Finished gathering info %s cells.', table.shape[0])
            table.to_csv(self.cache_location, sep='\t', index=False)
            self.write_lookup()
        else:
            logger.info('Retrieving cached cell info.')
            table = pd.read_csv(self.cache_location, sep='\t')
            self.load_lookup()
        return table

    def get_metadata(self, sample_id, fov):
        """
        :param sample_id: The sample identifier for the given whole image.
        :type sample_id: str

        :param fov: The string identifying a given field of view in the whole image.
        :type fov: str

        :return: A table containing metadata about all the cells in the given field of
            view. The format is specified by instantiating the table_header_template
            once for each phenotype/channel described by the given dataset_design.
        :rtype: pandas.DataFrame
        """
        c = self.cells
        sample_id_index = self.get_sample_id_index(sample_id)
        fov_index = self.get_fov_index(sample_id, fov)
        sample_col = CellMetadata.table_header_constant_portion['Sample ID index column name']
        fov_col = CellMetadata.table_header_constant_portion['Field of view index column name']
        return c[(c[sample_col] == sample_id_index) & (c[fov_col] == fov_index)]
