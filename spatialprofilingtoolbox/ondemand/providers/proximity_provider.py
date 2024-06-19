"""Proximity calculation from pairs of signatures."""

from typing import cast

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.ondemand.phenotype_str import (\
    phenotype_str_to_phenotype,
    phenotype_to_phenotype_str,
)
from spatialprofilingtoolbox.ondemand.providers.pending_provider import PendingProvider
from spatialprofilingtoolbox.ondemand.providers.provider import CellDataArrays
from spatialprofilingtoolbox.db.describe_features import get_feature_description
from spatialprofilingtoolbox.workflow.common.proximity import \
    compute_proximity_metric_for_signature_pair
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class ProximityProvider(PendingProvider):
    """Do proximity calculation from pair of signatures."""

    def compute(self) -> None:
        args, arrays = self._prepare_parameters()
        if arrays.identifiers is None:
            self.handle_insert_value(None, allow_null=True)
        else:
            value = self._perform_computation(args, arrays)
            self.handle_insert_value(value, allow_null=True)

    def _prepare_parameters(
        self,
    ) -> tuple[tuple[PhenotypeCriteria, PhenotypeCriteria, float], CellDataArrays]:
        study = self.job.study
        feature_specification = str(self.job.feature_specification)
        _, specifiers = ProximityProvider.retrieve_specifiers(study, feature_specification)
        phenotype1 = phenotype_str_to_phenotype(specifiers[0])
        phenotype2 = phenotype_str_to_phenotype(specifiers[1])
        radius = float(specifiers[2])
        arrays = self.get_cell_data_arrays()
        return (phenotype1, phenotype2, radius), arrays

    def _perform_computation(self, args: tuple, arrays: CellDataArrays) -> float | None:
        phenotype1, phenotype2, radius = args
        return compute_proximity_metric_for_signature_pair(
            phenotype1,
            phenotype2,
            radius,
            arrays.phenotype,
            arrays.location,
            arrays.feature_names,
        )

    @classmethod
    def get_or_create_feature_specification(
        cls,
        study: str,
        data_analysis_study: str,
        phenotype1: PhenotypeCriteria | None = None,
        phenotype2: PhenotypeCriteria | None = None,
        radius: float | None = None,
        **kwargs,
    ) -> tuple[str, bool]:
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
            return (specification, False)
        message = 'Creating feature with specifiers: (%s) %s, %s, %s'
        logger.debug(message, *specifiers_arguments)
        return (cls._create_feature_specification(study, *specifiers_arguments), True)

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
