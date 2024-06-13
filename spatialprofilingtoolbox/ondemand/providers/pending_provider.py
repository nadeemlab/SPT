"""Abstract class for providers that need to wait for on demand calculations to complete."""

from abc import ABC
from abc import abstractmethod
from threading import Thread
from datetime import datetime
from math import isnan
from math import isinf

from pandas import DataFrame

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.accessors.study import StudyAccess
from spatialprofilingtoolbox.ondemand.providers.provider import OnDemandProvider
from spatialprofilingtoolbox.ondemand.scheduler import MetricComputationScheduler
from spatialprofilingtoolbox.workflow.common.export_features import \
    ADIFeatureSpecificationUploader
from spatialprofilingtoolbox.workflow.common.export_features import add_feature_value
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class PendingProvider(OnDemandProvider, ABC):
    """Provide precalculated metrics or start, wait, receive, and then provide them."""

    @classmethod
    def get_metrics_or_schedule(
        cls,
        study: str,
        **kwargs,
    ) -> dict[str, dict[str, float | None] | bool]:
        """Get requested metrics, computed up to now."""
        with DBCursor(study=study) as cursor:
            get = ADIFeatureSpecificationUploader.get_data_analysis_study
            measurement_study_name = StudyAccess(cursor).get_study_components(study).measurement
            data_analysis_study = get(measurement_study_name, cursor)
        get_or_create = cls.get_or_create_feature_specification
        feature_specification = get_or_create(study, data_analysis_study, **kwargs)
        if cls._is_already_computed(study, feature_specification):
            is_pending = False
            logger.info('Already computed.')
        else:
            is_pending = cls._is_already_pending(study, feature_specification)
            if is_pending:
                logger.info('Already pending.')
            else:
                logger.info('Not already pending.')
            if not is_pending:
                cls._set_pending_computation(study, feature_specification)
                scheduler = MetricComputationScheduler(None)
                scheduler.schedule_feature_computation(study, int(feature_specification))
                is_pending = True
        return cls._query_for_computed_feature_values(
            study,
            feature_specification,
            still_pending=is_pending,
        )

    def insert_value(self, value: float | int) -> None:
        study = self.job.study
        specification = str(self.job.feature_specification)
        sample = self.job.sample
        with DBCursor(study=study) as cursor:
            add_feature_value(specification, sample, str(value), cursor)
        if self._is_already_computed(study, specification):
            self.drop_pending_computation(study, specification)
            logger.info(f'Finished computing feature {specification} ({study}).')

    @classmethod
    @abstractmethod
    def get_or_create_feature_specification(
        cls,
        study: str,
        data_analysis_study: str,
        **kwargs,
    ) -> str:
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
    def _is_already_computed(study: str, feature_specification: str) -> bool:
        get_expected = PendingProvider._get_expected_number_of_computed_values
        expected = get_expected(study, feature_specification)
        get_actual = PendingProvider._get_actual_number_of_computed_values
        actual = get_actual(study, feature_specification)
        logger.debug('Actual / expected total values: %s / %s', actual, expected)
        if actual < expected:
            return False
        if actual == expected:
            return True
        message = 'Possibly too many computed values of the given type?'
        raise ValueError(f'{message} Feature "{feature_specification}"')

    @staticmethod
    def _get_expected_number_of_computed_values(study: str, feature_specification: str) -> int:
        get_domain = PendingProvider._get_expected_domain_for_computed_values
        domain = get_domain(study, feature_specification)
        number = len(domain)
        return number

    @staticmethod
    def relevant_specimens_query() -> str:
        return '''
            SELECT DISTINCT sdmp.specimen FROM specimen_data_measurement_process sdmp
            JOIN study_component sc1 ON sc1.component_study=sdmp.study
            JOIN study_component sc2 ON sc1.primary_study=sc2.primary_study
            JOIN feature_specification fsn ON fsn.study=sc2.component_study
            WHERE fsn.identifier=%s
        '''

    @staticmethod
    def _get_expected_domain_for_computed_values(
        study: str,
        feature_specification: str,
    ) -> list[str]:
        with DBCursor(study=study) as cursor:
            query = PendingProvider.relevant_specimens_query()
            cursor.execute(f'{query};', (feature_specification,))
            rows = cursor.fetchall()
        return [row[0] for row in rows]

    @staticmethod
    def _get_actual_number_of_computed_values(study: str, feature_specification: str) -> int:
        with DBCursor(study=study) as cursor:
            cursor.execute('''
            SELECT COUNT(*) FROM quantitative_feature_value qfv
            WHERE qfv.feature=%s AND qfv.value IS NOT NULL
            ;
            ''', (feature_specification,))
            rows = cursor.fetchall()
            return rows[0][0]

    @classmethod
    def _is_already_pending(cls, study: str, feature_specification: str) -> bool:
        with DBCursor(study=study) as cursor:
            cursor.execute('''
            SELECT * FROM pending_feature_computation pfc
            WHERE pfc.feature_specification=%s
            ''', (feature_specification,))
            rows = cursor.fetchall()
        if len(rows) >= 1:
            return True
        return False

    @classmethod
    def _set_pending_computation(cls, study: str, feature_specification: str) -> None:
        time_str = datetime.now().ctime()
        with DBCursor(study=study) as cursor:
            cursor.execute('''
                INSERT INTO pending_feature_computation (feature_specification, time_initiated)
                VALUES (%s, %s) ;
                ''',
               (feature_specification, time_str),
            )

    @classmethod
    def drop_pending_computation(cls, study: str, feature_specification: str) -> None:
        """Drop note that the computation is still pending."""
        with DBCursor(study=study) as cursor:
            cursor.execute('''
                DELETE FROM pending_feature_computation pfc
                WHERE pfc.feature_specification=%s ;
                ''',
                (feature_specification, ),
            )

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
    ) -> dict[str, dict[str, float | None] | bool]:
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
                row[0]: _json_compliant_float(row[1])
                for row in rows
            }
        return {
            'metrics': metrics,
            'pending': still_pending,
        }

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
    if value:
        floated = float(value)
        if not (isnan(floated) or isinf(floated)):
            return floated
    return None
