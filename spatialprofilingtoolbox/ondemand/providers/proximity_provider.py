"""Proximity calculation from pairs of signatures."""

from threading import Thread
from datetime import datetime

import numpy as np
from sklearn.neighbors import BallTree

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.ondemand.phenotype_str import phenotype_str_to_phenotype
from spatialprofilingtoolbox.ondemand.phenotype_str import phenotype_to_phenotype_str
from spatialprofilingtoolbox.ondemand.providers import Provider
from spatialprofilingtoolbox.workflow.common.export_features import ADIFeatureSpecificationUploader
from spatialprofilingtoolbox.workflow.common.export_features import add_feature_value
from spatialprofilingtoolbox.workflow.common.proximity import \
    describe_proximity_feature_derivation_method
from spatialprofilingtoolbox.workflow.common.proximity import \
    compute_proximity_metric_for_signature_pair
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class ProximityProvider(Provider):
    """Do proximity calculation from pair of signatures."""

    def __init__(self, data_directory: str, load_centroids: bool = False) -> None:
        """Load from a precomputed JSON artifact in the data directory.

        Note: ProximityProvider always loads centroids because it needs them.
        """
        super().__init__(data_directory, load_centroids=True)

        logger.info('Start loading location data and creating ball trees.')
        self.create_ball_trees(self.centroids)
        logger.info('Finished creating ball trees.')

        del self.centroids

    def create_ball_trees(self, centroids):
        self.trees = {
            study_name: {
                sample_identifier: BallTree(np.array(points_list))
                for sample_identifier, points_list in points_lists.items()
            }
            for study_name, points_lists in centroids.items()
        }

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
        with DBCursor() as cursor:
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
        feature_specifications = {row[0]: [] for row in rows}
        for row in rows:
            feature_specifications[row[0]].append(row[1])
        for key, specifiers in feature_specifications.items():
            if len(specifiers) == 3:
                return key
        message = 'Creating feature with specifiers: (%s) %s, %s, %s'
        logger.debug(message, study_name, phenotype1_str,
                     phenotype2_str, radius)
        specification = ProximityProvider.create_feature_specification(
            study_name,
            phenotype1_str,
            phenotype2_str,
            radius,
        )
        return specification

    @staticmethod
    def create_feature_specification(study_name, phenotype1, phenotype2, radius):
        specifiers = [phenotype1, phenotype2, str(radius)]
        method = describe_proximity_feature_derivation_method()
        with DBCursor() as cursor:
            Uploader = ADIFeatureSpecificationUploader
            feature_specification = Uploader.add_new_feature(
                specifiers, method, study_name, cursor)
        return feature_specification

    @staticmethod
    def is_already_computed(feature_specification):
        expected = ProximityProvider.get_expected_number_of_computed_values(
            feature_specification)
        actual = ProximityProvider.get_actual_number_of_computed_values(
            feature_specification)
        if actual < expected:
            return False
        if actual == expected:
            return True
        message = 'Possibly too many computed values of the given type?'
        raise ValueError(f'{message} Feature "{feature_specification}"')

    @staticmethod
    def get_expected_number_of_computed_values(feature_specification):
        domain = ProximityProvider.get_expected_domain_for_computed_values(
            feature_specification)
        number = len(domain)
        logger.debug('Number of values possible to be computed: %s', number)
        return number

    @staticmethod
    def get_expected_domain_for_computed_values(feature_specification):
        with DBCursor() as cursor:
            cursor.execute('''
            SELECT DISTINCT sdmp.specimen FROM specimen_data_measurement_process sdmp
            JOIN study_component sc1 ON sc1.component_study=sdmp.study
            JOIN study_component sc2 ON sc1.primary_study=sc2.primary_study
            JOIN feature_specification fsn ON fsn.study=sc2.component_study
            WHERE fsn.identifier=%s
            ;
            ''', (feature_specification,))
            rows = cursor.fetchall()
        return [row[0] for row in rows]

    @staticmethod
    def get_actual_number_of_computed_values(feature_specification):
        with DBCursor() as cursor:
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
        with DBCursor() as cursor:
            cursor.execute('''
            SELECT * FROM pending_feature_computation pfc
            WHERE pfc.feature_specification=%s
            ''', (feature_specification,))
            rows = cursor.fetchall()
        if len(rows) >= 1:
            return True
        return False

    @staticmethod
    def retrieve_specifiers(feature_specification):
        with DBCursor() as cursor:
            cursor.execute('''
            SELECT fs.specifier, fs.ordinality
            FROM feature_specifier fs
            WHERE fs.feature_specification=%s ;
            ''', (feature_specification,))
            rows = cursor.fetchall()
            specifiers = [row[0]
                          for row in sorted(rows, key=lambda row: int(row[1]))]
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
        with DBCursor() as cursor:
            cursor.execute('''
            INSERT INTO pending_feature_computation (feature_specification, time_initiated)
            VALUES (%s, %s) ;
            ''', (feature_specification, time_str))

    @staticmethod
    def drop_pending_computation(feature_specification):
        with DBCursor() as cursor:
            cursor.execute('''
            DELETE FROM pending_feature_computation pfc
            WHERE pfc.feature_specification=%s ;
            ''', (feature_specification, ))

    def do_proximity_metrics_one_feature(self, feature_specification):
        specifiers = ProximityProvider.retrieve_specifiers(
            feature_specification)
        study_name, phenotype1, phenotype2, radius = specifiers
        sample_identifiers = self.get_sample_identifiers(feature_specification)
        for sample_identifier in sample_identifiers:
            value = compute_proximity_metric_for_signature_pair(
                phenotype1,
                phenotype2,
                radius,
                self.get_cells(sample_identifier, study_name),
                self.get_tree(sample_identifier, study_name),
            )
            message = 'Computed one feature value of %s: %s, %s'
            logger.debug(message, feature_specification,
                         sample_identifier, value)
            with DBCursor() as cursor:
                add_feature_value(feature_specification,
                                  sample_identifier, value, cursor)
        ProximityProvider.drop_pending_computation(feature_specification)
        message = 'Wrapped up proximity metric calculation, feature "%s".'
        logger.debug(message, feature_specification)
        logger.debug('The samples considered were: %s', sample_identifiers)

    @staticmethod
    def query_for_computed_feature_values(feature_specification, still_pending=False):
        with DBCursor() as cursor:
            cursor.execute('''
            SELECT qfv.subject, qfv.value
            FROM quantitative_feature_value qfv
            WHERE qfv.feature=%s
            ''', (feature_specification,))
            rows = cursor.fetchall()
            metrics = {row[0]: float(row[1]) if row[1]
                       else None for row in rows}
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
            is_pending = False
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

    @staticmethod
    def get_sample_identifiers(feature_specification):
        return ProximityProvider.get_expected_domain_for_computed_values(feature_specification)
