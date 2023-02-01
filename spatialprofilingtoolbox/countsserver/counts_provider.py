"""
Do cell counting for a specific signature, over the specially-created
binary-format index.
"""
import sys
import re
import os
from os.path import join
import json

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CountsProvider:
    """Scan binary-format expression matrices for specific signatures."""

    def __init__(self, data_directory):
        self.load_expressions_indices(data_directory)
        self.load_data_matrices(data_directory)
        logger.info('countsserver is ready to accept connections.')

    def load_expressions_indices(self, data_directory):
        logger.debug('Searching for source data in: %s', data_directory)
        json_files = [f for f in os.listdir(data_directory) if os.path.isfile(
            join(data_directory, f)) and re.search(r'\.json$', f)]
        if len(json_files) != 1:
            logger.error('Did not find index JSON file.')
            sys.exit(1)
        with open(join(data_directory, json_files[0]), 'rt', encoding='utf-8') as file:
            root = json.loads(file.read())
            entries = root[list(root.keys())[0]]
            self.studies = {}
            for entry in entries:
                self.studies[entry['specimen measurement study name']] = entry

    def load_data_matrices(self, data_directory):
        self.data_arrays = {}
        for study_name in self.get_study_names():
            self.data_arrays[study_name] = {
                item['specimen']: self.get_data_array_from_file(
                    join(data_directory, item['filename']))
                for item in self.studies[study_name]['expressions files']
            }

    def get_study_names(self):
        return self.studies.keys()

    def get_data_array_from_file(self, filename):
        data_array = []
        with open(filename, 'rb') as file:
            buffer = None
            while buffer != b'':
                buffer = file.read(8)
                data_array.append(int.from_bytes(buffer, 'little'))
        return data_array

    def compute_signature(self, channel_names, study_name):
        target_by_symbol = self.studies[study_name]['target by symbol']
        target_index_lookup = self.studies[study_name]['target index lookup']
        if not all(name in target_by_symbol.keys() for name in channel_names):
            return None
        identifiers = [target_by_symbol[name] for name in channel_names]
        indices = [target_index_lookup[identifier]
                   for identifier in identifiers]
        signature = 0
        for index in indices:
            signature = signature + (1 << index)
        return signature

    def count_structures_of_exact_signature(self, signature, study_name):
        counts = {}
        for specimen, data_array in self.data_arrays[study_name].items():
            count = 0
            for entry in data_array:
                if entry == signature:
                    count = count + 1
            counts[specimen] = [count, len(data_array)]
        return counts

    def count_structures_of_partial_signature(self, signature, study_name):
        counts = {}
        for specimen, data_array in self.data_arrays[study_name].items():
            count = 0
            for entry in data_array:
                if entry | signature == entry:
                    count = count + 1
            counts[specimen] = [count, len(data_array)]
        return counts

    def count_structures_of_partial_signed_signature(
            self, positives_signature, negatives_signature, study_name):
        counts = {}
        for specimen, data_array in self.data_arrays[study_name].items():
            count = 0
            for entry in data_array:
                if (entry | positives_signature == entry) and \
                        (~entry | negatives_signature == ~entry):
                    count = count + 1
            counts[specimen] = [count, len(data_array)]
        return counts

    def get_status(self):
        return [
            {
                'study': study_name,
                'counts by channel': [
                    {
                        'channel symbol': symbol,
                        'count': self.count_structures_of_partial_signed_signature(
                            [symbol], [], study_name),
                    }
                    for symbol in sorted(list(targets['target by symbol'].keys()))
                ],
                'total number of cells': len(self.data_arrays[study_name]),
            }
            for study_name, targets in self.studies.items()
        ]

    def has_study(self, study_name):
        return study_name in self.studies
