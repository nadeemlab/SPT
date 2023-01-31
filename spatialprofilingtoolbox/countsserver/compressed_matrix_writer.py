"""
Utility for writing expression matrices in a specially-compressed binary
format.
"""
import re
import random
import json

from spatialprofilingtoolbox.workflow.common.sparse_matrix_puller import CompressedDataArrays
from spatialprofilingtoolbox.countsserver.defaults import EXPRESSIONS_INDEX_FILENAME
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CompressedMatrixWriter:
    """Write the compressed in-memory binary format matrices to file."""
    def write(self, data_arrays: CompressedDataArrays):
        self.write_data_arrays(data_arrays)
        self.write_index(data_arrays)
        self.report_subsample_for_inspection(data_arrays)

    def write_data_arrays(self, data_arrays: CompressedDataArrays):
        _, study_indices = self.get_study_names_and_indices(data_arrays)
        for study_name, study in data_arrays.get_studies().items():
            study_index = study_indices[study_name]
            specimen, specimen_indices = self.get_specimens_and_indices(
                study_name, data_arrays)
            for specimen, data_array in study['data arrays by specimen'].items():
                specimen_index = specimen_indices[specimen]
                filename = '.'.join([
                    self.get_data_array_filename_base(),
                    str(study_index),
                    str(specimen_index),
                    'bin',
                ])
                self.write_data_array_to_file(data_array, filename)

    def write_index(self, data_arrays: CompressedDataArrays):
        index = []
        _, study_indices = self.get_study_names_and_indices(
            data_arrays)
        for study_name in sorted(list(data_arrays.get_studies().keys())):
            study = data_arrays.get_studies()[study_name]
            index_item = {}
            index_item['specimen measurement study name'] = study_name
            index_item['expressions files'] = []
            study_index = study_indices[study_name]
            specimen, specimen_indices = self.get_specimens_and_indices(
                study_name, data_arrays)
            for specimen in study['data arrays by specimen']:
                specimen_index = specimen_indices[specimen]
                filename = '.'.join([
                    self.get_data_array_filename_base(),
                    str(study_index),
                    str(specimen_index),
                    'bin',
                ])
                index_item['expressions files'].append({
                    'specimen': specimen,
                    'filename': filename,
                })
            index_item['target index lookup'] = study['target index lookup']
            index_item['target by symbol'] = study['target by symbol']
            index.append(index_item)
        with open(EXPRESSIONS_INDEX_FILENAME, 'wt', encoding='utf-8') as index_file:
            index_file.write(json.dumps({'': index}, indent=4))
        logger.debug('Wrote expression index file %s .',
                     EXPRESSIONS_INDEX_FILENAME)

    def get_study_names_and_indices(self, data_arrays: CompressedDataArrays):
        study_names = sorted(list(data_arrays.get_studies().keys()))
        return study_names, {s: i for i, s in enumerate(study_names)}

    def get_specimens_and_indices(self, study_name, data_arrays: CompressedDataArrays):
        study = data_arrays.get_studies()[study_name]
        specimens = sorted(list(study['data arrays by specimen'].keys()))
        return [
            specimens,
            {s: i for i, s in enumerate(specimens)},
        ]

    def get_data_array_filename_base(self):
        return 'expression_data_array'

    def write_data_array_to_file(self, data_array, filename):
        with open(filename, 'wb') as file:
            for entry in data_array:
                file.write(entry.to_bytes(8, 'little'))

    def report_subsample_for_inspection(self, data_arrays: CompressedDataArrays):
        size = 20
        logger.debug('%s randomly sampled vectors:', size)
        study_name = list(data_arrays.get_studies().keys())[0]
        data_arrays = data_arrays.get_studies()[study_name]['data arrays by specimen']
        data_array = list(data_arrays.values())[0]
        for _ in range(size):
            value = data_array[random.choice(range(len(data_array)))]
            print(''.join(list(reversed(re.sub('0', ' ', f'{value:064b}')))))
