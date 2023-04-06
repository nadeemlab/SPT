"""
Provides proximity metric computation on demand across whole database.
"""
# import datetime
import re

from sklearn.neighbors import BallTree

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor
from spatialprofilingtoolbox.workflow.common.proximity import \
    compute_proximity_metric_for_signature_pair
# from spatialprofilingtoolbox.workflow.common.proximity import \
#     describe_proximity_feature_derivation_method
# from spatialprofilingtoolbox.workflow.common.export_features import ADIFeaturesUploader
# from spatialprofilingtoolbox.workflow.common.proximity import validate_value
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class ProximityCalculator:
    """
    Provides functionality to request computation of proximity of specific
    phenotypes, and to give back these features if already computed.
    """
    def __init__(self, study, database_config_file):
        logger.info(
            'Start pulling feature matrix data for proximity on-demand calculator, study %s.',
            study)
        bundle = FeatureMatrixExtractor.extract(database_config_file=database_config_file,
                                                study=study)
        logger.info('Finished pulling data for %s.', study)

        for identifier, sample in list(bundle[study]['feature matrices'].items()):
            logger.info('Cells dataframe for %s has size %s', identifier, sample['dataframe'].shape)
        study_bundle = bundle[study]
        self.cells_by_sample = {
            sample_identifier: sample['dataframe']
            for sample_identifier, sample in study_bundle['feature matrices'].items()
        }

        self.channel_symbols_by_column_name = bundle[study]['channel symbols by column name']
        self.channels = sorted(self.channel_symbols_by_column_name.values())

        logger.info('Start creating ball trees.')
        self.create_ball_trees(bundle[study])
        logger.info('Finished creating ball trees.')
        self.study_name = study
        self.database_config_file = database_config_file
        self.cached_metrics = None

    def get_study_name(self):
        return self.study_name

    def get_database_config_file(self):
        return self.database_config_file

    def request_computation(self, phenotype1, phenotype2, radius):
        logger.debug('Requesting computation.')
        signature1 = self.retrieve_signature(phenotype1)
        signature2 = self.retrieve_signature(phenotype2)
        metrics = {
            sample_identifier:
            compute_proximity_metric_for_signature_pair(signature1,
                                                        signature2,
                                                        radius,
                                                        self.get_cells(sample_identifier),
                                                        self.get_tree(sample_identifier))
            for sample_identifier in self.get_sample_identifiers()
        }
        self.cache_metrics(metrics)

    def cache_metrics(self, metrics):
        self.cached_metrics = metrics

    def retrieve_signature(self, phenotype):
        signature = None
        if phenotype in self.channels:
            signature = {'positive': [phenotype], 'negative': []}
        if re.match(r'^\d+$', phenotype):
            signature = self.get_signature_of_cell_phenotype(phenotype)
        if signature is None:
            raise ValueError(f'Phenotype {phenotype} could not be looked up.')
        column_name_by_channel_symbol = {
            value: key
            for key, value in self.channel_symbols_by_column_name.items()
        }
        return {
            sign: [column_name_by_channel_symbol[m] for m in markers]
            for sign, markers in signature.items()
        }

    def get_signature_of_cell_phenotype(self, phenotype_identifier):
        query = '''
        SELECT cs.symbol, cpc.polarity
        FROM cell_phenotype_criterion cpc
        JOIN study_component sc ON sc.component_study=cpc.study
        JOIN chemical_species cs ON cs.identifier=cpc.marker
        WHERE sc.primary_study=%s AND cpc.cell_phenotype=%s
        ;
        '''
        with DatabaseConnectionMaker(self.get_database_config_file()) as dcm:
            connection = dcm.get_connection()
            cursor = connection.cursor()
            cursor.execute(query, (self.get_study_name(), phenotype_identifier))
            rows = cursor.fetchall()
            return {
                sign: [row[0] for row in rows if row[1] == sign]
                for sign in ['positive', 'negative']
            }

    def get_sample_identifiers(self):
        return self.cells_by_sample.keys()

    def get_cells(self, sample_identifier):
        return self.cells_by_sample[sample_identifier]

    def get_tree(self, sample_identifier):
        return self.trees[sample_identifier]

    def retrieve_cached_metrics(self):
        return self.cached_metrics

    def create_ball_trees(self, study_bundle):
        self.trees = {
            sample_identifier: BallTree(sample['dataframe'][['pixel x', 'pixel y']].to_numpy())
            for sample_identifier, sample in study_bundle['feature matrices'].items()
        }


def get_study_names(database_config_file):
    with DatabaseConnectionMaker(database_config_file=database_config_file) as dcm:
        connection = dcm.get_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT study_specifier FROM study;')
        rows = cursor.fetchall()
    return [str(row[0]) for row in rows]


def get_proximity_calculator(database_config_file, study_name):
    return ProximityCalculator(study_name, database_config_file)
