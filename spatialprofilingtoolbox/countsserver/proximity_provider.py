"""
Do proximity calculation from pair of signatures.
"""
import sys
import re
import os
from os.path import join
import json

import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree

from spatialprofilingtoolbox.workflow.common.structure_centroids import StructureCentroids
from spatialprofilingtoolbox.workflow.common.proximity import \
    compute_proximity_metric_for_signature_pair
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class ProximityProvider:
    """Do proximity calculation from pair of signatures."""

    def __init__(self, data_directory):
        self.data_directory = data_directory
        self.load_expressions_indices()

        loader = StructureCentroids()
        loader.load_from_file(self.get_data_directory())
        centroids = loader.get_studies()

        self.load_data_matrices(centroids)
        logger.info('ProximityProvider is finished loading source expression data.')

        logger.info('Start loading location data and creating ball trees.')
        self.create_ball_trees(centroids)
        logger.info('Finished creating ball trees.')

    def get_data_directory(self):
        return self.data_directory

    def load_expressions_indices(self):
        logger.debug('Searching for source data in: %s', self.get_data_directory())
        json_files = [
            f for f in os.listdir(self.get_data_directory())
            if os.path.isfile(join(self.get_data_directory(), f)) and re.search(r'\.json$', f)
        ]
        if len(json_files) != 1:
            logger.error('Did not find index JSON file.')
            sys.exit(1)
        index_file = join(self.get_data_directory(), json_files[0])
        with open(index_file, 'rt', encoding='utf-8') as file:
            root = json.loads(file.read())
            entries = root[list(root.keys())[0]]
            self.studies = {}
            for entry in entries:
                self.studies[entry['specimen measurement study name']] = entry

    def load_data_matrices(self, centroids):
        self.data_arrays = {}
        for study_name in self.get_study_names():
            self.data_arrays[study_name] = {
                item['specimen']:
                self.get_data_array_from_file(
                    join(self.get_data_directory(), item['filename']),
                    self.studies[study_name]['target index lookup'],
                    self.studies[study_name]['target by symbol'],
                    study_name,
                    item['specimen'],
                    centroids,
                )
                for item in self.studies[study_name]['expressions files']
            }
            shapes = [df.shape for df in self.data_arrays[study_name].values()]
            logger.debug('Loaded dataframes of sizes %s', shapes)

    def create_ball_trees(self, centroids):
        self.trees = {
            study_name: {
                sample_identifier: BallTree(np.array(points_list))
                for sample_identifier, points_list in points_lists.items()
            }
            for study_name, points_lists in centroids.items()
        }

    def get_study_names(self):
        return self.studies.keys()

    def get_data_array_from_file(self, filename, target_index_lookup, target_by_symbol, study_name,
                                 sample, centroids):
        rows = []
        columns = self.list_columns(target_index_lookup, target_by_symbol)
        with open(filename, 'rb') as file:
            buffer = None
            while buffer != b'':
                buffer = file.read(8)
                integer64 = int.from_bytes(buffer, 'little')
                row = list(map(int, list(bin(integer64)[2:].ljust(len(columns), '0'))))
                rows.append(row)
        df = pd.DataFrame(rows, columns=columns)
        df['pixel x'] = [point[0] for point in centroids[study_name][sample]]
        df['pixel y'] = [point[1] for point in centroids[study_name][sample]]
        return df

    def list_columns(self, target_index_lookup, target_by_symbol):
        target_by_index = {value: key for key, value in target_index_lookup.items()}
        symbol_by_target = {value: key for key, value in target_by_symbol.items()}
        return [
            symbol_by_target[target_by_index[i]]
            for i in range(len(target_by_index))
        ]

    def compute_metrics(self, study_name, phenotype1, phenotype2, radius):
        logger.debug('Requesting computation.')
        metrics = {
            sample_identifier:
            compute_proximity_metric_for_signature_pair(
                phenotype1,
                phenotype2,
                radius,
                self.get_cells(sample_identifier, study_name),
                self.get_tree(sample_identifier, study_name))
            for sample_identifier in self.get_sample_identifiers(study_name)
        }
        raise ValueError(f'Temporary debugging exception/breakpoint 2. {metrics}')
        return metrics

    def get_cells(self, sample_identifier, study_name):
        return self.data_arrays[study_name][sample_identifier]

    def get_tree(self, sample_identifier, study_name):
        return self.trees[study_name][sample_identifier]

    def get_sample_identifiers(self, study_name):
        return self.data_arrays[study_name].keys()

    def get_channels(self, study_name):
        key = list(self.get_sample_identifiers(study_name))[0]
        return list(self.data_arrays[study_name][key].columns)
