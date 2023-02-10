"""
Convenience provision of a feature matrix for each study, the data retrieved
from the SPT database.
"""
import sys

import pandas as pd

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.stratification_puller import StratificationPuller
from spatialprofilingtoolbox.workflow.common.structure_centroids_puller import \
    StructureCentroidsPuller
from spatialprofilingtoolbox.workflow.common.sparse_matrix_puller import SparseMatrixPuller
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class FeatureMatrixExtractor:
    """
    Pull from the database and create convenience bundle of feature matrices
    and metadata.
    """
    @staticmethod
    def extract(database_config_file, specimen: str=None):
        E = FeatureMatrixExtractor
        data_arrays = E.retrieve_expressions_from_database(database_config_file, specimen=specimen)
        centroid_coordinates = E.retrieve_structure_centroids_from_database(database_config_file,
                                                                            specimen=specimen)
        stratification = E.retrieve_derivative_stratification_from_database(database_config_file)
        study_component_lookup = E.retrieve_study_component_lookup(database_config_file)
        return E.merge_dictionaries(
            E.create_feature_matrices(data_arrays, centroid_coordinates),
            E.create_channel_information(data_arrays),
            stratification,
            new_keys=['feature matrices','channel symbols by column name', 'sample cohorts'],
            study_component_lookup=study_component_lookup,
        )

    @staticmethod
    def redact_dataframes(extraction):
        for study_name, study in extraction.items():
            for specimen in study['feature matrices'].keys():
                extraction[study_name]['feature matrices'][specimen]['dataframe'] = None
            extraction[study_name]['sample cohorts']['assignments'] = None
            extraction[study_name]['sample cohorts']['strata'] = None

    @staticmethod
    def retrieve_expressions_from_database(database_config_file, specimen: str=None):
        logger.info('Retrieving expression data from database.')
        with SparseMatrixPuller(database_config_file) as puller:
            puller.pull(specimen=specimen)
            data_arrays = puller.get_data_arrays()
        logger.info('Done retrieving expression data from database.')
        return data_arrays.get_studies()

    @staticmethod
    def retrieve_structure_centroids_from_database(database_config_file, specimen: str=None):
        logger.info('Retrieving polygon centroids from shapefiles in database.')
        with StructureCentroidsPuller(database_config_file) as puller:
            puller.pull(specimen=specimen)
            structure_centroids = puller.get_structure_centroids()
        logger.info('Done retrieving centroids.')
        return structure_centroids.get_studies()

    @staticmethod
    def retrieve_derivative_stratification_from_database(database_config_file):
        logger.info('Retrieving stratification from database.')
        with StratificationPuller(database_config_file=database_config_file) as puller:
            puller.pull()
            stratification = puller.get_stratification()
        logger.info('Done retrieving stratification.')
        return stratification

    @staticmethod
    def retrieve_study_component_lookup(database_config_file):
        with DatabaseConnectionMaker(database_config_file=database_config_file) as maker:
            connection = maker.get_connection()
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM study_component ; ')
            rows = cursor.fetchall()
            cursor.close()
        lookup = {}
        for row in rows:
            lookup[row[1]] = row[0]
        return lookup

    @staticmethod
    def create_feature_matrices(data_arrays, centroid_coordinates):
        logger.info(
            'Creating feature matrices from binary data arrays and centroids.')
        matrices = {}
        for k, study_name in enumerate(sorted(list(data_arrays.keys()))):
            study = data_arrays[study_name]
            matrices[study_name] = {}
            for j, specimen in enumerate(sorted(list(study['data arrays by specimen'].keys()))):
                logger.debug('Specimen %s .', specimen)
                expressions = study['data arrays by specimen'][specimen]
                number_channels = len(study['target index lookup'])
                rows = [
                    FeatureMatrixExtractor.create_feature_matrix_row(
                        centroid_coordinates[study_name][specimen][i],
                        expressions[i],
                        number_channels,
                    )
                    for i in range(len(expressions))
                ]
                dataframe = pd.DataFrame(
                    rows,
                    columns=['pixel x', 'pixel y'] +
                    [f'F{i}' for i in range(number_channels)])
                matrices[study_name][specimen] = {
                    'dataframe': dataframe,
                    'filename': f'{k}.{j}.tsv',
                }
        logger.info('Done creating feature matrices.')
        return matrices

    @staticmethod
    def create_feature_matrix_row(centroid, binary, number_channels):
        template = '{0:0%sb}' % number_channels   # pylint: disable=consider-using-f-string
        feature_vector = [int(value) for value in list(template.format(binary)[::-1])]
        return [centroid[0], centroid[1]] + feature_vector

    @staticmethod
    def create_channel_information(data_arrays):
        return {
            study_name: FeatureMatrixExtractor.create_channel_information_for_study(study)
            for study_name, study in data_arrays.items()
        }

    @staticmethod
    def create_channel_information_for_study(study):
        logger.info('Aggregating channel information for one study.')
        targets = {int(index): target for target,
                   index in study['target index lookup'].items()}
        symbols = {target: symbol for symbol,
                   target in study['target by symbol'].items()}
        logger.info('Done aggregating channel information.')
        return {
            f'F{i}': symbols[targets[i]]
            for i in sorted([int(index) for index in targets.keys()])
        }

    @staticmethod
    def merge_dictionaries(*args, new_keys: list, study_component_lookup: dict):
        if not len(args) == len(new_keys):
            logger.error(
                "Can not match up dictionaries to be merged with the list of key names to be "
                "issued for them.")
            sys.exit(1)

        merged = {}
        for i in range(len(new_keys)):
            for substudy, value in args[i].items():
                merged[study_component_lookup[substudy]] = {}

        for i, key in enumerate(new_keys):
            for substudy, value in args[i].items():
                merged[study_component_lookup[substudy]][key] = value

        logger.info('Done merging into a single dictionary bundle.')
        return merged
