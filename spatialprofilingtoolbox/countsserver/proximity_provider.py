"""
Do proximity calculation from pair of signatures.
"""
import sys
import re
import os
from os.path import join
import json
from threading import Thread
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree

from spatialprofilingtoolbox.apiserver.app.db_accessor import DBAccessor
from spatialprofilingtoolbox.countsserver.phenotype_str import phenotype_str_to_phenotype
from spatialprofilingtoolbox.countsserver.phenotype_str import phenotype_to_phenotype_str
from spatialprofilingtoolbox.workflow.common.export_features import ADIFeatureSpecificationUploader
from spatialprofilingtoolbox.workflow.common.export_features import add_feature_value
from spatialprofilingtoolbox.workflow.common.proximity import \
    describe_proximity_feature_derivation_method
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
            while True:
                buffer = file.read(8)
                if buffer == b'':
                    break
                binary_expression_64_string = ''.join([''.join(list(reversed(bin(ii)[2:].rjust(8,'0')))) for ii in buffer])
                binary_expression_truncated_to_channels = binary_expression_64_string[0:len(columns)]
                row = [int(b) for b in list(binary_expression_truncated_to_channels)]
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

    @staticmethod
    def get_or_create_feature_specification(study_name, phenotype1, phenotype2, radius):
        phenotype1_str = phenotype_to_phenotype_str(phenotype1)
        phenotype2_str = phenotype_to_phenotype_str(phenotype2)
        args = (
            study_name,
            phenotype1_str,
            phenotype2_str,
            str(radius),
            describe_proximity_feature_derivation_method(),
        )
        with DBAccessor() as db_accessor:
            connection = db_accessor.get_connection()
            cursor = connection.cursor()
            cursor.execute('''
            SELECT
                fsn.identifier,
                fs.specifier
            FROM feature_specification fsn
            JOIN feature_specifier fs ON fs.feature_specification=fsn.identifier
            JOIN study_component sc ON sc.component_study=fsn.study
            JOIN study_component sc2 ON sc2.primary_study=sc.primary_study
            WHERE sc2.component_study=%s AND
                  (   (fs.specifier=%s AND fs.ordinality='1')
                   OR (fs.specifier=%s AND fs.ordinality='2')
                   OR (fs.specifier=%s AND fs.ordinality='3') ) AND
                  fsn.derivation_method=%s
            ;
            ''', args)
            rows = cursor.fetchall()
            cursor.close()
        feature_specifications = {row[0]: [] for row in rows}
        for row in rows:
            feature_specifications[row[0]].append(row[1])
        for key, specifiers in feature_specifications.items():
            if len(specifiers) == 3:
                return key
        logger.debug('Creating feature with specifiers: (%s) %s, %s, %s', study_name, phenotype1_str, phenotype2_str, radius)
        specification = ProximityProvider.create_feature_specification(study_name, phenotype1_str, phenotype2_str, radius)
        return specification

    @staticmethod
    def create_feature_specification(study_name, phenotype1, phenotype2, radius):
        specifiers = [phenotype1, phenotype2, str(radius)]
        method = describe_proximity_feature_derivation_method()
        with DBAccessor() as db_accessor:
            connection = db_accessor.get_connection()
            cursor = connection.cursor()
            feature_specification = ADIFeatureSpecificationUploader.add_new_feature(
                specifiers, method, study_name, cursor)
            cursor.close()
            connection.commit()
        return feature_specification

    @staticmethod
    def is_already_computed(feature_specification):
        expected = ProximityProvider.get_expected_number_of_computed_values(feature_specification)
        actual = ProximityProvider.get_actual_number_of_computed_values(feature_specification)
        if actual < expected:
            return False
        if actual == expected:
            return True
        raise ValueError(f'Possibly too many computed values of the given type? Feature "{feature_specification}"')

    @staticmethod
    def get_expected_number_of_computed_values(feature_specification):
        with DBAccessor() as db_accessor:
            connection = db_accessor.get_connection()
            cursor = connection.cursor()
            cursor.execute('''
            SELECT COUNT(DISTINCT sdmp.specimen) FROM specimen_data_measurement_process sdmp
            JOIN study_component sc1 ON sc1.component_study=sdmp.study
            JOIN study_component sc2 ON sc1.primary_study=sc2.primary_study
            JOIN feature_specification fsn ON fsn.study=sc2.component_study
            WHERE fsn.identifier=%s
            ;
            ''', (feature_specification,))
            rows = cursor.fetchall()
            logger.debug('Number of values possible to be computed: %s', rows[0][0])
            cursor.close()            
            return rows[0][0]

    @staticmethod
    def get_actual_number_of_computed_values(feature_specification):
        with DBAccessor() as db_accessor:
            connection = db_accessor.get_connection()
            cursor = connection.cursor()
            cursor.execute('''
            SELECT COUNT(*) FROM quantitative_feature_value qfv
            WHERE qfv.feature=%s
            ;
            ''', (feature_specification,))
            rows = cursor.fetchall()
            logger.debug('Actual number computed: %s', rows[0][0])
            return rows[0][0]

    @staticmethod
    def is_already_pending(feature_specification):
        with DBAccessor() as db_accessor:
            connection = db_accessor.get_connection()
            cursor = connection.cursor()
            cursor.execute('''
            SELECT * FROM pending_feature_computation pfc
            WHERE pfc.feature_specification=%s
            ''', (feature_specification,))
            rows = cursor.fetchall()
        if len(rows) >=1:
            return True
        return False

    @staticmethod
    def retrieve_specifiers(feature_specification):
        with DBAccessor() as db_accessor:
            connection = db_accessor.get_connection()
            cursor = connection.cursor()
            cursor.execute('''
            SELECT fs.specifier, fs.ordinality
            FROM feature_specifier fs
            WHERE fs.feature_specification=%s ;
            ''', (feature_specification,))
            rows = cursor.fetchall()
            specifiers = [row[0] for row in sorted(rows, key=lambda row: int(row[1]))]
            cursor.execute('''
            SELECT sc2.component_study FROM feature_specification fs
            JOIN study_component sc ON sc.component_study=fs.study
            JOIN study_component sc2 ON sc.primary_study=sc2.primary_study
            WHERE fs.identifier=%s AND
                sc2.component_study IN ( SELECT name FROM specimen_measurement_study )
                ;
            ''', (feature_specification,))
            study = cursor.fetchall()[0][0]
        return [
            study,
            phenotype_str_to_phenotype(specifiers[0]),
            phenotype_str_to_phenotype(specifiers[1]),
            float(specifiers[2]),
        ]

    def fork_computation_task(self, feature_specification):
        background_thread = Thread(
            target=self.do_proximity_metrics_one_feature,
            args=(feature_specification,)
        )
        background_thread.start()

    @staticmethod
    def set_pending_computation(feature_specification):
        time_str = datetime.now().ctime()
        with DBAccessor() as db_accessor:
            connection = db_accessor.get_connection()
            cursor = connection.cursor()
            cursor.execute('''
            INSERT INTO pending_feature_computation (feature_specification, time_initiated)
            VALUES (%s, %s) ;
            ''', (feature_specification, time_str))
            cursor.close()
            connection.commit()

    @staticmethod
    def drop_pending_computation(feature_specification):
        with DBAccessor() as db_accessor:
            connection = db_accessor.get_connection()
            cursor = connection.cursor()
            cursor.execute('''
            DELETE FROM pending_feature_computation pfc
            WHERE pfc.feature_specification=%s ;
            ''', (feature_specification, ))
            cursor.close()
            connection.commit()

    def do_proximity_metrics_one_feature(self, feature_specification):
        specifiers = ProximityProvider.retrieve_specifiers(feature_specification)
        study_name, phenotype1, phenotype2, radius = specifiers
        for sample_identifier in self.get_sample_identifiers(study_name):
            value = compute_proximity_metric_for_signature_pair(
                phenotype1,
                phenotype2,
                radius,
                self.get_cells(sample_identifier, study_name),
                self.get_tree(sample_identifier, study_name),
            )
            logger.debug('Computed one feature value of %s: %s, %s', feature_specification, sample_identifier, value)
            with DBAccessor() as db_accessor:
                connection = db_accessor.get_connection()
                cursor = connection.cursor()
                add_feature_value(feature_specification, sample_identifier, value, cursor)
                cursor.close()
                connection.commit()
        ProximityProvider.drop_pending_computation(feature_specification)
        logger.debug('Wrapped up proximity metric calculation, feature "%s".', feature_specification)

    @staticmethod
    def query_for_computed_feature_values(feature_specification, still_pending=False):
        with DBAccessor() as db_accessor:
            connection = db_accessor.get_connection()
            cursor = connection.cursor()
            cursor.execute('''
            SELECT qfv.subject, qfv.value
            FROM quantitative_feature_value qfv
            WHERE qfv.feature=%s
            ''', (feature_specification,))
            rows = cursor.fetchall()
            metrics = {row[0]: float(row[1]) for row in rows}
        return {
            'metrics': metrics,
            'pending': still_pending,
        }

    def compute_metrics(self, study_name, phenotype1, phenotype2, radius):
        logger.debug('Requesting computation.')
        PP = ProximityProvider
        feature_specification = PP.get_or_create_feature_specification(
            study_name, phenotype1, phenotype2, radius)
        if PP.is_already_computed(feature_specification):
            is_pending=False
            logger.debug('Already computed.')
        else:
            is_pending = PP.is_already_pending(feature_specification)
            if is_pending:
                logger.debug('Already already pending.')
            else:
                logger.debug('Not already pending.')
            if not is_pending:
                logger.debug('Starting background task.')
                self.fork_computation_task(feature_specification)
                PP.set_pending_computation(feature_specification)
                logger.debug('Background task just started, is pending.')
                is_pending = True
        return PP.query_for_computed_feature_values(feature_specification, still_pending=is_pending)

    def get_cells(self, sample_identifier, study_name):
        return self.data_arrays[study_name][sample_identifier]

    def get_tree(self, sample_identifier, study_name):
        return self.trees[study_name][sample_identifier]

    def get_sample_identifiers(self, study_name):
        return self.data_arrays[study_name].keys()

    def get_channels(self, study_name):
        key = list(self.get_sample_identifiers(study_name))[0]
        return list(self.data_arrays[study_name][key].columns)
