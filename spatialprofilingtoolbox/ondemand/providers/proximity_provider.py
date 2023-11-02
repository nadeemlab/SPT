"""Proximity calculation from pairs of signatures."""

from typing import cast

from pandas import DataFrame
from sklearn.neighbors import BallTree  # type: ignore

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.ondemand.phenotype_str import (\
    phenotype_str_to_phenotype,
    phenotype_to_phenotype_str,
)
from spatialprofilingtoolbox.ondemand.providers.pending_provider import PendingProvider
from spatialprofilingtoolbox.workflow.common.export_features import add_feature_value
from spatialprofilingtoolbox.db.describe_features import get_feature_description
from spatialprofilingtoolbox.workflow.common.proximity import (\
    compute_proximity_metric_for_signature_pair,
)
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class ProximityProvider(PendingProvider):
    """Do proximity calculation from pair of signatures."""

    def __init__(self, data_directory: str, timeout: int, load_centroids: bool = False) -> None:
        """Load from a precomputed JSON artifact in the data directory.

        Note: ProximityProvider always loads centroids because it needs them.
        """
        super().__init__(data_directory, timeout, load_centroids=True)

        logger.info('Start loading location data and creating ball trees.')
        self._dropna_in_data_arrays()
        self._create_ball_trees()
        logger.info('Finished creating ball trees.')

    @classmethod
    def service_specifier(cls) -> str:
        return 'proximity'

    def _dropna_in_data_arrays(self) -> None:
        for _, _data_arrays in self.data_arrays.items():
            for sample_identifier, df in _data_arrays.items():
                former = df.shape
                df.dropna(inplace=True)
                current = df.shape
                if current[0] != former[0]:
                    defect0 = former[0] - current[0]
                    message = f'Dropped {defect0} rows due to to NAs, for {sample_identifier}.'
                    logger.info(message)
                if current[1] != former[1]:
                    defect1 = former[1] - current[1]
                    message = f'Dropped {defect1} columns due to to NAs, for {sample_identifier}.'
                    logger.warning(message)

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
        study: str,
        data_analysis_study: str,
        phenotype1: PhenotypeCriteria | None = None,
        phenotype2: PhenotypeCriteria | None = None,
        radius: float | None = None,
        **kwargs,
    ) -> str:
        phenotype1 = cast(PhenotypeCriteria, phenotype1)
        phenotype2 = cast(PhenotypeCriteria, phenotype2)
        radius = cast(float, radius)
        specifiers_arguments = (
            data_analysis_study,
            phenotype_to_phenotype_str(phenotype1),
            phenotype_to_phenotype_str(phenotype2),
            str(radius),
        )
        specification = cls._get_feature_specification(study, *specifiers_arguments)
        if specification is not None:
            return specification
        message = 'Creating feature with specifiers: (%s) %s, %s, %s'
        logger.debug(message, *specifiers_arguments)
        return cls._create_feature_specification(study, *specifiers_arguments)

    @classmethod
    def _get_feature_specification(cls,
        study: str,
        data_analysis_study: str,
        phenotype1_str: str,
        phenotype2_str: str,
        radius_str: str,
    ) -> str | None:
        args = (
            data_analysis_study,
            phenotype1_str,
            phenotype2_str,
            radius_str,
            get_feature_description('proximity'),
        )
        with DBCursor(study=study) as cursor:
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
        feature_specifications: dict[str, list[str]] = {row[0]: [] for row in rows}
        for row in rows:
            feature_specifications[row[0]].append(row[1])
        for key, specifiers in feature_specifications.items():
            if len(specifiers) == 3:
                return key
        return None

    @classmethod
    def _create_feature_specification(cls,
        study: str,
        data_analysis_study: str,
        phenotype1: str,
        phenotype2: str,
        radius: str,
    ) -> str:
        specifiers = (phenotype1, phenotype2, str(radius))
        method = get_feature_description('proximity')
        return cls.create_feature_specification(study, specifiers, data_analysis_study, method)

    def have_feature_computed(self, study: str, feature_specification: str) -> None:
        args = (study, feature_specification)
        data_analysis_study, specifiers = ProximityProvider.retrieve_specifiers(study, feature_specification)
        phenotype1 = phenotype_str_to_phenotype(specifiers[0])
        phenotype2 = phenotype_str_to_phenotype(specifiers[1])
        radius = float(specifiers[2])
        sample_identifiers = ProximityProvider.get_sample_identifiers(study, feature_specification)
        use_nulls = False
        for sample_identifier in sample_identifiers:
            if not use_nulls:
                value = compute_proximity_metric_for_signature_pair(
                    phenotype1,
                    phenotype2,
                    radius,
                    self.get_cells(sample_identifier, data_analysis_study),
                    self._get_tree(sample_identifier, data_analysis_study),
                )
            else:
                value = None
            message = 'Computed one feature value of %s: %s, %s'
            logger.debug(message, feature_specification, sample_identifier, value)
            with DBCursor(study=study) as cursor:
                add_feature_value(feature_specification, sample_identifier, value, cursor)
            if self.check_timeout(*args):
                use_nulls = True
        ProximityProvider.drop_pending_computation(study, feature_specification)
        message = 'Wrapped up proximity metric calculation, feature "%s".'
        logger.debug(message, feature_specification)
        logger.debug('The samples considered were: %s', sample_identifiers)

    def _get_tree(self, sample_identifier: str, data_analysis_study: str) -> BallTree:
        return self.trees[data_analysis_study][sample_identifier]
