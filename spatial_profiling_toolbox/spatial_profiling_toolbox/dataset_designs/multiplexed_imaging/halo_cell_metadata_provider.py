import os
from os.path import join
import re

import pandas as pd

from ...environment.cell_metadata import CellMetadata
from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class SampleFOVLookup:
    """
    A wrapper around indices of sample identifier / field of view pairs. Supports
    replacing the potentially long string identifiers with integers in certain
    contexts.
    """
    def __init__(self):
        self.sample_ids = []
        self.fov_descriptors = {}

    def add_sample_id(self, sample_id):
        if sample_id not in self.sample_ids:
            self.sample_ids.append(sample_id)
            self.fov_descriptors[sample_id] = []

    def add_fovs(self, sample_id, fovs):
        for fov in fovs:
            fov = str(fov)
            if fov not in self.fov_descriptors[sample_id]:
                self.fov_descriptors[sample_id].append(fov)

    def get_sample_index(self, sample_id):
        return self.sample_ids.index(sample_id)

    def get_fov_index(self, sample_id, fov):
        return self.fov_descriptors[sample_id].index(fov)


class HALOCellMetadata(CellMetadata):
    """
    An object to efficiently hold all cell metadata for a large bundle of source
    files in HALO-exported format.
    """
    def __init__(self, **kwargs):
        super(HALOCellMetadata, self).__init__(**kwargs)
        self.lookup = None

    def get_sample_id_index(self, sample_id):
        return self.lookup.get_sample_index(sample_id)

    def get_fov_index(self, sample_id, fov):
        return self.lookup.get_fov_index(sample_id, fov)

    def get_cell_info_table(self, input_files_path, file_metadata, dataset_design):
        if not self.check_data_type(file_metadata, dataset_design):
            return
        self.lookup = SampleFOVLookup()
        dfs = []
        for i, row in file_metadata.iterrows():
            data_type = row['Data type']
            if not data_type == dataset_design.get_cell_manifest_descriptor():
                continue
            filename = row['File name']
            sample_id = row['Sample ID']
            source_file_data = pd.read_csv(join(input_files_path, filename))
            if dataset_design.get_FOV_column() not in source_file_data.columns:
                logger.error(
                    '%s not in columns of %s. Got %s',
                    dataset_design.get_FOV_column(),
                    filename,
                    source_file_data.columns,
                )
                break
            self.populate_integer_indices(
                lookup=self.lookup,
                sample_id=sample_id,
                fovs=source_file_data[dataset_design.get_FOV_column()],
            )

            column_data, number_cells = self.get_selected_columns(
                dataset_design,
                self.lookup,
                source_file_data,
                sample_id,
            )
            dfs.append(pd.DataFrame(column_data))
            logger.debug(
                'Finished pulling metadata for %s cells from source file %s/%s.',
                number_cells,
                i+1,
                file_metadata.shape[0],
            )
        return pd.concat(dfs)

    def check_data_type(self, file_metadata, dataset_design):
        """
        Args:
            file_metadata (pandas.DataFrame):
                Table of cell manifest files.

        Returns:
            bool:
                True if this class supports all the file data types stipulated by the
                file metadata records. False otherwise.
        """
        if not 'Data type' in file_metadata.columns:
            logger.error('File metadata table missing columns "Data type".')
            return False
        data_types = list(set(file_metadata['Data type']))
        expected_data_type = dataset_design.get_cell_manifest_descriptor()
        if not ( (len(data_types) == 1) and (data_types[0] == expected_data_type) ):
            logger.warning(
                'Expected entries "%s" in "Data type" field, got %s.',
                expected_data_type,
                data_types,
            )
            if not expected_data_type in data_types:
                logger.error(
                    'Did not get the expected data type: %s',
                    expected_data_type,
                )
                return False
        return True

    def populate_integer_indices(self,
            lookup: SampleFOVLookup=None,
            sample_id: str=None,
            fovs=None
        ):
        """
        Registers integer indices for a group of fields of view for a given sample
        / whole image.

        Args:
            lookup (SampleFOVLookup):
                The lookup object to save to.
            sample_id (str):
                A sample identifier string, as it would appear in the file metadata
                manifest.
            fovs (list):
                A list of field of view descriptor strings, as they appear in
                HALO-exported source files.
        """
        lookup.add_sample_id(sample_id)
        lookup.add_fovs(sample_id, fovs)

    def get_selected_columns(self, dataset_design, lookup, source_file_data, sample_id):
        """
        Retrieves, from an unprocessed source file table, only the data which is
        stipulated to be relevant according to this class' table header templates.

        Args:
            dataset_design:
                The wrapper object describing the input dataset.
            lookup (SampleFOVLookup):
                The integer index lookup table.
            source_file_data (pandas.DataFrame):
                The full, unprocessed table of data from a given source file.
            sample_id (str):
                The sample identifier identifying the sample that the given source file
                has data about.
        """
        column_data = {}
        v = CellMetadata.table_header_template
        c = CellMetadata.table_header_constant_portion
        d = dataset_design

        sample_id_index = lookup.get_sample_index(sample_id)
        N = source_file_data.shape[0]
        sample_id_indices = [sample_id_index] * N
        fov_indices = list(source_file_data.apply(
            lambda row: lookup.get_fov_index(sample_id, row[d.get_FOV_column()]),
            axis=1,
        ))
        column_data[c['Sample ID index column name']] = sample_id_indices
        column_data[c['Field of view index column name']] = fov_indices

        phenotype_names = d.get_elementary_phenotype_names()
        for name in phenotype_names:
            origin = d.get_feature_name(name)
            target = re.sub('{{channel specifier}}', name, v['positivity column name'])
            column_data[target] = source_file_data[origin]

        for name in phenotype_names:
            target = re.sub('{{channel specifier}}', name, v['intensity column name'])
            column_data[target] = d.get_combined_intensity(source_file_data, name)

        return [column_data, N]

