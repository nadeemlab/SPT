import os
from os.path import exists, join
import re

import pandas as pd

from ...environment.cell_metadata import CellMetadata
from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class HALOCellMetadata(CellMetadata):
    def __init__(self, **kwargs):
        super(HALOCellMetadata, self).__init__(**kwargs)

    def get_cell_info_table(self, cache_location, input_files_path, file_metadata, input_data_design):
        d = input_data_design
        if not 'Data type' in file_metadata.columns:
            logger.error('File metadata table missing columns "Data type".')
            return
        data_types = list(set(file_metadata['Data type']))
        expected_data_type = 'HALO software cell manifest'
        if not ( (len(data_types) == 1) and (data_types[0] == expected_data_type) ):
            logger.error('Expected "%s" in "Data type" field, got %s', expected_data_type, data_types)
            return

        sample_ids = []
        fov_descriptors = {}
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

            if sample_id not in sample_ids:
                sample_ids.append(sample_id)
                fov_descriptors[sample_id] = []

            fovs = source_file_data[d.get_FOV_column()]
            for fov in fovs:
                fov = str(fov)
                if fov not in fov_descriptors[sample_id]:
                    fov_descriptors[sample_id].append(fov)

            column_data = {}
            v = CellMetadata.table_header_template
            c = CellMetadata.table_header_constant_portion

            sample_id_index = sample_ids.index(sample_id)
            N = source_file_data.shape[0]
            sample_id_indices = [sample_id_index] * N
            fov_descriptors_i = fov_descriptors[sample_id]
            fov_indices = list(source_file_data.apply(lambda row: fov_descriptors_i.index(row[d.get_FOV_column()]), axis=1))
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
