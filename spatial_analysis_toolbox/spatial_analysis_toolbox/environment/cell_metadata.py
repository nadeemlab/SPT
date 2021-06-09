import os
from os.path import exists

import pandas as pd

from .log_formats import colorized_logger

logger = colorized_logger(__name__)


class CellMetadata:
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
            input_files_path: str=None,
            input_data_design=None,
            cache_location: str=None,
            file_manifest_file: str=None,
        ):
        """
        Args:
            input_data_design:
                Object providing get_elementary_phenotype_names, get_pandas_signature,
                get_combined_intensity, and get_box_limit_column_names.

            file_manifest_file (str):
                Path to the manifest of source files containing cell-level information.
        """
        self.input_files_path = input_files_path
        self.input_data_design = input_data_design
        if cache_location is None:
            self.cache_location = CellMetadata.default_cache_location
        else:
            self.cache_location = cache_location
        self.file_manifest_file = file_manifest_file
        self.file_metadata = pd.read_csv(file_manifest_file, sep='\t')
        self.cells = pd.DataFrame()

    def initialize(self):
        self.cells = self.load_cache_file()

    def load_cache_file(self):
        """
        If not yet cached, creates table of cells from source files listed in the given
        file manifest, then caches this to file.

        Else loads directly from file.

        Returns:
            df (pandas.DataFrame):
                The table of cell metadata. The format should be as described by
                get_metadata.
        """
        f = self.cache_location
        if not exists(f):
            logger.info('Gathering cell info from files listed in %s', self.file_manifest_file)
            df = self.get_cell_info_table(
                f,
                self.input_files_path,
                self.file_metadata,
                self.input_data_design,
            )
            logger.info('Finished gathering info %s cells.', df.shape[0])
            df.to_csv(f, sep='\t', index=False)
        else:
            logger.info('Retrieving cached cell info.')
            df = pd.read_csv(f, sep='\t')
        return df

    def get_cell_info_table(self, cache_location, input_files_path, file_metadata, input_data_design):
        """
        Returns:
            df (pandas.DataFrame):
                The table of cell metadata. The format should be as described by
                get_metadata.
        """
        pass

    def get_metadata(self, sample_id, fov):
        """
        Args:
            sample_id (str):
                The sample identifier for the given whole image.

            fov (str):
                The string identifying a given field of view in the whole image.

        Returns:
            df (pandas.DataFrame):
                A table containing metadata about all the cells in the given field of
                view. The format is specified by instantiating the table_header_template
                once for each phenotype/channel described by the given input_data_design.
        """
        c = self.cells
        return c[(c['Sample ID'] == sample_id) & (c['Field of view'] == fov)]
