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
            cache_location: str=None,
        ):
        """
        Args:

            dataset_design:
                Object providing get_elementary_phenotype_names, get_pandas_signature,
                get_combined_intensity, and get_box_limit_column_names.
            file_manifest_file (str):
                Path to the manifest of source files containing cell-level information.
            input_file_path (str):
                The path to the directory containing the input files described the
                file manifest.
            cache_location (str):
                (Optional) An alternative file location to cache the cell-related
                tables.
        """
        self.input_files_path = input_files_path
        self.dataset_design = dataset_design
        if cache_location is None:
            self.cache_location = CellMetadata.default_cache_location
        else:
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
        Args:
            input_files_path (str):
                Path to directory containing input files described by the file manifest.
            file_metadata (pandas.DataFrame):
                Table of file metadata, from file_manifest_file.
            dataset_design:
                Dataset design object.

        Returns:
            pandas.DataFrame:
                The table of cell metadata. The format should be as described by
                get_metadata.
        """
        pass

    def get_sample_id_index(self, sample_id):
        """
        Args:
            sample_id (str):
                A sample identifier.

        Returns:
            int:
                The integer index of the sample identifier.
        """
        pass

    def get_fov_index(self, sample_id, fov):
        """
        Args:
            sample_id (str):
                A sample identifier.
            fov (str):
                A field of view identifier string.

        Returns:
            int:
                The integer index of the field of view in the given sample.
        """
        pass

    def load_cache_file(self):
        """
        If not yet cached, creates table of cells from source files listed in the given
        file manifest, then caches this to file.

        Otherwise, loads directly from the cache file.

        Returns:
            pandas.DataFrame:
                The table of cell metadata. The format should be as described by
                get_metadata.
        """
        f = self.cache_location
        if not exists(f):
            logger.info('Gathering cell info from files listed in %s', self.file_manifest_file)
            df = self.get_cell_info_table(
                self.input_files_path,
                self.file_metadata,
                self.dataset_design,
            )
            logger.info('Finished gathering info %s cells.', df.shape[0])
            df.to_csv(f, sep='\t', index=False)
        else:
            logger.info('Retrieving cached cell info.')
            df = pd.read_csv(f, sep='\t')
        return df

    def get_metadata(self, sample_id, fov):
        """
        Args:
            sample_id (str):
                The sample identifier for the given whole image.

            fov (str):
                The string identifying a given field of view in the whole image.

        Returns:
            pandas.DataFrame:
                A table containing metadata about all the cells in the given field of
                view. The format is specified by instantiating the table_header_template
                once for each phenotype/channel described by the given dataset_design.
        """
        c = self.cells
        sample_id_index = self.get_sample_id_index(sample_id)
        fov_index = self.get_fov_index(sample_id, fov)
        sample_col = CellMetadata.table_header_constant_portion['Sample ID index column name']
        fov_col = CellMetadata.table_header_constant_portion['Field of view index column name']
        return c[(c[sample_col] == sample_id_index) & (c[fov_col] == fov_index)]
