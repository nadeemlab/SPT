import os
from os.path import exists, join
import re

import pandas as pd

from ...environment.cell_metadata import CellMetadata
from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class SampleFOVLookup:
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
    def __init__(self, **kwargs):
        super(HALOCellMetadata, self).__init__(**kwargs)

    def get_cell_info_table(self, cache_location, input_files_path, file_metadata, input_data_design):
        if not self.check_data_type(file_metadata):
            return

        d = input_data_design
        lookup = SampleFOVLookup()
        v = CellMetadata.table_header_template
        c = CellMetadata.table_header_constant_portion
        dfs = []
        for i, row in file_metadata.iterrows():
            filename = row['File name']
            sample_id = row['Sample ID']
            source_file_data = pd.read_csv(join(input_files_path, filename))

            if d.get_FOV_column() not in source_file_data.columns:
                logger.error(
                    '%s not in columns of %s. Got %s',
                    d.get_FOV_column(),
                    filename,
                    source_file_data.columns,
                )
                break

            self.populate_integer_indices(
                lookup=lookup,
                sample_id=sample_id,
                fovs=source_file_data[d.get_FOV_column()],
            )

            column_data = {}
            sample_id_index = lookup.get_sample_index(sample_id)
            N = source_file_data.shape[0]
            sample_id_indices = [sample_id_index] * N
            fov_indices = list(source_file_data.apply(lambda row: lookup.get_fov_index(sample_id, row[d.get_FOV_column()]), axis=1))
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

            df_i = pd.DataFrame(column_data)
            dfs.append(df_i)
            logger.debug('Finished pulling metadata for %s cells from source file %s/%s.', df_i.shape[0], i+1, file_metadata.shape[0])
        return pd.concat(dfs)

    def check_data_type(self, file_metadata):
        if not 'Data type' in file_metadata.columns:
            logger.error('File metadata table missing columns "Data type".')
            return False
        data_types = list(set(file_metadata['Data type']))
        expected_data_type = 'HALO software cell manifest'
        if not ( (len(data_types) == 1) and (data_types[0] == expected_data_type) ):
            logger.error('Expected "%s" in "Data type" field, got %s', expected_data_type, data_types)
            return False
        return True

    def populate_integer_indices(self,
            lookup: SampleFOVLookup=None,
            sample_id=None,
            fovs=None
        ):
        lookup.add_sample_id(sample_id)
        lookup.add_fovs(sample_id, fovs)
