"""Abstract class for providers that need to wait for on demand calculations to complete."""

from abc import ABC
from abc import abstractmethod
from datetime import datetime
from math import isnan
from math import isinf

from spatialprofilingtoolbox.db.database_connection import DBCursor
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
    ) -> UnivariateMetricsComputationResult:
        """Get requested metrics, computed up to now."""
        with DBCursor(study=study) as cursor:
            get = ADIFeatureSpecificationUploader.get_data_analysis_study
            measurement_study_name = StudyAccess(cursor).get_study_components(study).measurement
            data_analysis_study = get(measurement_study_name, cursor)
        get_or_create = cls.get_or_create_feature_specification
        feature_specification, is_new = get_or_create(study, data_analysis_study, **kwargs)
        if not is_new and cls._no_outstanding_jobs(study, feature_specification):
            logger.info(f'Cache hit for feature {feature_specification}, because there are no outstanding computation jobs for it.')
            return cls._query_for_computed_feature_values(
                study,
                feature_specification,
                still_pending=False,
            )
        was_pending = not cls._no_outstanding_jobs(study, feature_specification)
        no_outstanding_jobs = cls._no_outstanding_jobs(study, feature_specification)
        should_be_scheduled = is_new and no_outstanding_jobs
        if should_be_scheduled:
            scheduler = MetricComputationScheduler(None)
            scheduler.schedule_feature_computation(study, int(feature_specification))
        was_scheduled = should_be_scheduled
        is_pending = should_be_scheduled or was_pending
        return cls._query_for_computed_feature_values(
            study,
            feature_specification,
            still_pending=is_pending,
        )

    @classmethod
    def _no_outstanding_jobs(cls, study: str, feature_specification: str) -> bool:
        with DBCursor(study=study) as cursor:
            query = 'SELECT COUNT(*) FROM quantitative_feature_value_queue WHERE feature=%s ;'
            cursor.execute(query, (feature_specification,))
            count = tuple(cursor.fetchall())[0][0]
        return count == 0

    def handle_insert_value(self, value: float | None) -> None:
        if value is not None:
            self.insert_value(value)
        else:
            self._warn_no_value()

    def _warn_no_value(self) -> None:
        specification = str(self.job.feature_specification)
        study = self.job.study
        sample = self.job.sample
        logger.warning(f'Feature {specification} ({sample}, {study}) could not be computed.')
        with DBCursor(study=study) as cursor:
            add_feature_value(specification, sample, None, cursor)

    def insert_value(self, value: float | int) -> None:
        study = self.job.study
        specification = str(self.job.feature_specification)
        sample = self.job.sample
        with DBCursor(study=study) as cursor:
            add_feature_value(specification, sample, str(value), cursor)
        self._wrap_up_feature()

    def _wrap_up_feature(self) -> None:
        study = self.job.study
        specification = str(self.job.feature_specification)
        if self._no_outstanding_jobs(study, specification):
            logger.info(f'Finished computing feature {specification} ({study}).')

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
        return UnivariateMetricsComputationResult(
            values = metrics,
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
