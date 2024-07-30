"""Abstract class for providers that need to wait for on demand calculations to complete."""

from abc import ABC
from abc import abstractmethod
from datetime import datetime
from math import isnan
from math import isinf

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import DBConnection
from spatialprofilingtoolbox.db.accessors.study import StudyAccess
from spatialprofilingtoolbox.ondemand.providers.provider import OnDemandProvider
from spatialprofilingtoolbox.ondemand.scheduler import MetricComputationScheduler
from spatialprofilingtoolbox.workflow.common.export_features import \
    ADIFeatureSpecificationUploader
from spatialprofilingtoolbox.workflow.common.export_features import add_feature_value
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import \
    UnivariateMetricsComputationResult
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class PendingProvider(OnDemandProvider, ABC):
    """Provide precalculated metrics or start, wait, receive, and then provide them."""

    @classmethod
    def get_metrics_or_schedule(
        cls,
        study: str,
        **kwargs,
    ) -> tuple[UnivariateMetricsComputationResult, str]:
        """Get requested metrics, computed up to now."""
        with DBCursor(study=study) as cursor:
            get = ADIFeatureSpecificationUploader.get_data_analysis_study
            measurement_study_name = StudyAccess(cursor).get_study_components(study).measurement
            data_analysis_study = get(measurement_study_name, cursor)
        get_or_create = cls.get_or_create_feature_specification
        feature_specification, is_new = get_or_create(study, data_analysis_study, **kwargs)
        all_jobs_complete = cls._all_jobs_complete(study, feature_specification)
        if is_new and all_jobs_complete:
            fs = feature_specification
            logger.warning(f'Newly created feature somehow has all jobs complete already ({fs}).')
        if all_jobs_complete:
            return (cls._query_for_computed_feature_values(
                study,
                feature_specification,
                still_pending=False,
            ), feature_specification)
        if is_new:
            scheduler = MetricComputationScheduler(None)
            scheduler.schedule_feature_computation(study, int(feature_specification))
        return (
            cls._query_for_computed_feature_values(
                study,
                feature_specification,
                still_pending=True,
            ),
            feature_specification,
        )

    @classmethod
    def _all_jobs_complete(cls, study: str, feature_specification: str) -> bool:
        with DBCursor(study=study) as cursor:
            query = 'SELECT COUNT(*) FROM quantitative_feature_value WHERE feature=%s ;'
            cursor.execute(query, (feature_specification,))
            count = tuple(cursor.fetchall())[0][0]
        expected = cls._get_expected_number_samples(study, feature_specification)
        if count > expected:
            message = f'Feature {feature_specification} has too many values, {count} / {expected}.'
            logger.warning(message)
        return count == expected

    @classmethod
    def _get_expected_number_samples(cls, study: str, feature_specification: str) -> int:
        return len(cls._get_expected_samples(study, feature_specification))

    @classmethod
    def _get_expected_samples(cls, study: str, feature_specification: str) -> tuple[str, ...]:
        with DBCursor(study=study) as cursor:
            query = cls.relevant_specimens_query() % f"'{feature_specification}'"
            cursor.execute(query)
            return tuple(map(lambda row: row[0], cursor.fetchall()))

    def handle_insert_value(self, value: float | None, allow_null: bool=True) -> None:
        if value is not None:
            self._insert_value(value)
        else:
            self._warn_no_value()
            if allow_null:
                self._insert_null()

    def _warn_no_value(self) -> None:
        specification = str(self.job.feature_specification)
        study = self.job.study
        sample = self.job.sample
        logger.warning(f'Feature {specification} ({sample}, {study}) could not be computed, worker generated None. May insert None.')

    def _insert_value(self, value: float | int) -> None:
        study = self.job.study
        specification = str(self.job.feature_specification)
        sample = self.job.sample
        with DBCursor(study=study) as cursor:
            add_feature_value(specification, sample, str(value), cursor)

    def _insert_null(self) -> None:
        study = self.job.study
        specification = str(self.job.feature_specification)
        sample = self.job.sample
        with DBCursor(study=study) as cursor:
            add_feature_value(specification, sample, None, cursor)

    @classmethod
    @abstractmethod
    def get_or_create_feature_specification(
        cls,
        study: str,
        data_analysis_study: str,
        **kwargs,
    ) -> tuple[str, bool]:
        """Return feature specification, creating one if necessary."""
        raise NotImplementedError("For subclasses to implement.")

    @staticmethod
    def create_feature_specification(
        study: str,
        specifiers: tuple[str, ...],
        data_analysis_study: str,
        method: str,
    ) -> str:
        with DBCursor(study=study) as cursor:
            Uploader = ADIFeatureSpecificationUploader
            add = Uploader.add_new_feature
            feature_specification = add(specifiers, method, data_analysis_study, cursor)
        return feature_specification

    @staticmethod
    def retrieve_specifiers(study: str, feature_specification: str) -> tuple[str, list[str]]:
        """Get specifiers for this feature specification."""
        with DBCursor(study=study) as cursor:
            cursor.execute('''
                SELECT fs.specifier, fs.ordinality
                FROM feature_specifier fs
                WHERE fs.feature_specification=%s ;
                ''',
                (feature_specification,),
            )
            rows = cursor.fetchall()
            specifiers = [row[0] for row in sorted(rows, key=lambda row: int(row[1]))]
            cursor.execute('''
                SELECT sc2.component_study FROM feature_specification fs
                JOIN study_component sc ON sc.component_study=fs.study
                JOIN study_component sc2 ON sc.primary_study=sc2.primary_study
                WHERE fs.identifier=%s AND
                    sc2.component_study IN ( SELECT name FROM specimen_measurement_study )
                    ;
                ''',
                (feature_specification,),
            )
            study = cursor.fetchall()[0][0]
        return study, specifiers

    @classmethod
    def _query_for_computed_feature_values(
        cls,
        study: str,
        feature_specification: str,
        still_pending: bool = False
    ) -> UnivariateMetricsComputationResult:
        with DBCursor(study=study) as cursor:
            cursor.execute('''
                SELECT qfv.subject, qfv.value
                FROM quantitative_feature_value qfv
                WHERE qfv.feature=%s
                ''',
                (feature_specification,),
            )
            rows = cursor.fetchall()
            metrics = {
                str(row[0]): _json_compliant_float(row[1])
                for row in rows
            }
            sorted_metrics = {key: metrics[key] for key in sorted(list(metrics.keys()))}
        return UnivariateMetricsComputationResult(
            values = sorted_metrics,
            is_pending = still_pending,
        )

    @classmethod
    def retrieve_feature_derivation_method(cls, study: str, feature_specification: str) -> str:
        with DBCursor(study=study) as cursor:
            cursor.execute('''
                SELECT derivation_method FROM feature_specification
                WHERE identifier=%s ;
                ''',
                (feature_specification,),
            )
            rows = cursor.fetchall()
        return rows[0][0]


def _json_compliant_float(value: str) -> float | None:
    if value is not None:
        floated = float(value)
        if not (isnan(floated) or isinf(floated)):
            return floated
    return None
