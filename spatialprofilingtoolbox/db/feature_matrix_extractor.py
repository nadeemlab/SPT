from difflib import SequenceMatcher

import pandas as pd

from ..standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)

from ..workflow.common.sparse_matrix_puller import SparseMatrixPuller
from ..workflow.common.structure_centroids_puller import StructureCentroidsPuller
from ..db.outcomes_puller import OutcomesPuller

class FeatureMatrixExtractor:
    @staticmethod
    def extract(database_config_file):
        E = FeatureMatrixExtractor
        data_arrays = E.retrieve_expressions_from_database(database_config_file)
        centroid_coordinates = E.retrieve_structure_centroids_from_database(database_config_file)
        outcomes = E.retrieve_derivative_outcomes_from_database(database_config_file)
        return E.merge_dictionaries(
            E.create_feature_matrices(data_arrays, centroid_coordinates),
            E.create_channel_information(data_arrays),
            outcomes,
            new_keys=['feature matrices', 'channel symbols by column name', 'outcomes']
        )

    @staticmethod
    def redact_dataframes(extraction):
        for study_name, study in extraction.items():
            for specimen in study['feature matrices'].keys():
                extraction[study_name]['feature matrices'][specimen]['dataframe'] = None
            extraction[study_name]['outcomes']['dataframe'] = None

    @staticmethod
    def retrieve_expressions_from_database(database_config_file):
        logger.info('Retrieving expression data from database.')
        with SparseMatrixPuller(database_config_file) as puller:
            puller.pull()
            data_arrays = puller.get_data_arrays()
        logger.info('Done retrieving expression data from database.')
        return data_arrays.studies

    @staticmethod
    def retrieve_structure_centroids_from_database(database_config_file):
        logger.info('Retrieving polygon centroids from shapefiles in database.')
        with StructureCentroidsPuller(database_config_file) as puller:
            puller.pull()
            structure_centroids = puller.get_structure_centroids()
        logger.info('Done retrieving centroids.')
        return structure_centroids.studies

    @staticmethod
    def retrieve_derivative_outcomes_from_database(database_config_file):
        logger.info('Retrieving outcomes from database.')
        with OutcomesPuller(database_config_file='../db/.spt_db.config.container') as puller:
            puller.pull()
            outcomes = puller.get_outcomes()
        logger.info('Done retrieving outcomes.')
        return outcomes

    @staticmethod
    def create_feature_matrices(data_arrays, centroid_coordinates):
        logger.info('Creating feature matrices from binary data arrays and centroids.')
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
                dataframe = pd.DataFrame(rows, columns=['pixel x', 'pixel y'] + ['F%s' % str(i) for i in range(number_channels)])
                matrices[study_name][specimen] = {
                    'dataframe' : dataframe,
                    'filename' : '%s.%s.tsv' % (str(k), str(j)),
                }
        logger.info('Done creating feature matrices.')
        return matrices

    @staticmethod
    def create_feature_matrix_row(centroid, binary, number_channels):
        return [centroid[0], centroid[1]] + [int(value) for value in list(('{0:0%sb}' % str(number_channels)).format(binary)[::-1])]

    @staticmethod
    def create_channel_information(data_arrays):
        return {
            study_name : FeatureMatrixExtractor.create_channel_information_for_study(study)
            for study_name, study in data_arrays.items()        
        }

    @staticmethod
    def create_channel_information_for_study(study):
        logger.info('Aggregating channel information for one study.')
        targets = { int(index) : target for target, index in study['target index lookup'].items() }
        symbols = { target : symbol for symbol, target in study['target by symbol'].items() }
        logger.info('Done aggregating channel information.')
        return {
            'F%s' % i : symbols[targets[i]]
            for i in sorted([int(index) for index in targets.keys()])
        }

    @staticmethod
    def merge_dictionaries(*args, new_keys=[]):
        if not len(args) == len(new_keys):
            logger.error("Can not match up dictionaries to be merged with the list of key names to be issued for them.")
            exit(1)
        prefix = None
        for dictionary in args:
            if set(dictionary.keys()) != set(args[0].keys()):
                logger.warn("Key sets for dictionaries to be merged do not match: %s %s", dictionary.keys(), args[0].keys())
                if len(dictionary) == 1 and len(args[0]) == 1:
                    logger.warn('Attempting to assume that there is just one study.')
                    prefix = FeatureMatrixExtractor.get_common_prefix(list(dictionary.keys())[0], list(args[0].keys())[0])
                else:
                    logger.error('Too many studies to guess an association.')
                    exit(1)
        if prefix != None:
            merged = {
                prefix : {
                    new_keys[i] : args[i][list(args[i].keys())[0]]
                    for i in range(len(new_keys))                
                }
            }
        else:
            merged = {}
            for key in args[0].keys():
                merged[key] = {
                    new_keys[i] : args[i][key]
                    for i in range(len(new_keys))
                }            
        logger.info('Done merging into a single dictionary bundle.')
        return merged

    @staticmethod
    def get_common_prefix(a, b):
        list1 = list(a)
        list2 = list(b)
        prefix = []
        for i in range(len(a)):
            if list1[i] == list2[i]:
                prefix.append(list1[i])
            else:
                break
        return ''.join(prefix)

