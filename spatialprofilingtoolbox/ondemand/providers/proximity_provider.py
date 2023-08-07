"""Proximity calculation from pairs of signatures."""

import numpy as np
from sklearn.neighbors import BallTree

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.ondemand.phenotype_str import (\
    phenotype_str_to_phenotype,
    phenotype_to_phenotype_str,
)
from spatialprofilingtoolbox.ondemand.providers import PendingProvider
from spatialprofilingtoolbox.workflow.common.export_features import (\
    ADIFeatureSpecificationUploader,
    add_feature_value,
)
from spatialprofilingtoolbox.workflow.common.proximity import (\
    describe_proximity_feature_derivation_method,
    compute_proximity_metric_for_signature_pair,
)
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class ProximityProvider(PendingProvider):
    """Do proximity calculation from pair of signatures."""

    def __init__(self, data_directory: str, load_centroids: bool = False) -> None:
        """Load from a precomputed JSON artifact in the data directory.

        Note: ProximityProvider always loads centroids because it needs them.
        """
        super().__init__(data_directory, load_centroids=True)

        logger.info('Start loading location data and creating ball trees.')
        self._create_ball_trees()
        logger.info('Finished creating ball trees.')

    def _create_ball_trees(self) -> None:
        self.trees = {
            study_name: {
                sample_identifier: BallTree(df[['pixel x', 'pixel y']].to_numpy())
                for sample_identifier, df in _data_arrays.items()
            }
            for study_name, _data_arrays in self.data_arrays.items()
        }

    @classmethod
    def get_or_create_feature_specification(
        cls,
        study_name: str,
        **kwargs: int | PhenotypeCriteria | list[PhenotypeCriteria]
    ) -> str:
        phenotype1_str = phenotype_to_phenotype_str(kwargs['phenotype1'])
        phenotype2_str = phenotype_to_phenotype_str(kwargs['phenotype2'])
        radius: int = kwargs['radius']
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
        specification = ProximityProvider._create_feature_specification(
            study_name,
            phenotype1_str,
            phenotype2_str,
            radius,
        )
        return specification

    @staticmethod
    def _create_feature_specification(
        study_name: str,
        phenotype1: str,
        phenotype2: str,
        radius: str,
    ) -> str:
        specifiers = [phenotype1, phenotype2, str(radius)]
        method = describe_proximity_feature_derivation_method()
        with DBCursor() as cursor:
            Uploader = ADIFeatureSpecificationUploader
            feature_specification = Uploader.add_new_feature(
                specifiers, method, study_name, cursor)
        return feature_specification

    def have_feature_computed(self, feature_specification: str) -> None:
        study_name, specifiers = ProximityProvider.retrieve_specifiers(
            feature_specification)
        phenotype1 = phenotype_str_to_phenotype(specifiers[0])
        phenotype2 = phenotype_str_to_phenotype(specifiers[1])
        radius = float(specifiers[2])
        sample_identifiers = ProximityProvider.get_sample_identifiers(feature_specification)
        for sample_identifier in sample_identifiers:
            value = compute_proximity_metric_for_signature_pair(
                phenotype1,
                phenotype2,
                radius,
                self.get_cells(sample_identifier, study_name),
                self._get_tree(sample_identifier, study_name),
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

    def _get_tree(self, sample_identifier: str, study_name: str) -> BallTree:
        return self.trees[study_name][sample_identifier]
