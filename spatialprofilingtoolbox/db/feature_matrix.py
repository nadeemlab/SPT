
from ..standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)

from ..workflow.common.sparse_matrix_puller import SparseMatrixPuller
from ..workflow.common.structure_centroids_puller import StructureCentroidsPuller

class FeatureMatrixExtractor:
    @staticmethod
    def extract(self, database_config_file):
        E = FeatureMatrixExtractor
        data_arrays = E.retrieve_expressions_from_database(database_config_file)
        centroid_coordinates = E.retrieve_structure_centroids_from_database(databases_config_file)
        outcomes = E.retrieve_derivative_outcomes_from_database(databases_config_file)
        return E.merge_dictionaries(
            E.create_feature_matrices(data_arrays, centroid_coordinates),
            outcomes,
            new_keys=['feature matrices', 'outcomes']
        )

    def retrieve_expressions_from_database(database_config_file):
        with SparseMatrixPuller(database_config_file) as puller:
            puller.pull()
            data_arrays = puller.get_data_arrays()
        return data_arrays

    def retrieve_structure_centroids_from_database(database_config_file):
        with StructureCentroidsPuller(database_config_file) as puller:
            puller.pull()
            structure_centroids = puller.get_structure_centroids()
        return structure_centroids

    def retrieve_derivative_outcomes_from_database(database_config_file):
        pass

    def create_feature_matrices(data_arrays, centroid_coordinates):
        pass

    def merge_dictionaries(*args, new_keys=[]):
        if not len(args) == len(new_keys):
            logger.error("Can not match up dictionaries to be merged with the list of key names to be issued for them.")
            exit(1)
        for dictionary in args:
            if set(dictionary.keys()) != set(args[0].keys()):
                logger.error("Key sets for dictionaries to be merged do not match: %s %s", dictionary.keys(), args[0].keys())
                exit(1)
        merged = {}
        for key in args[0].keys():
            merged[key] = {
                new_keys[i] : args[i][key]
                for i in range(len(new_keys))
            }
        return merged
