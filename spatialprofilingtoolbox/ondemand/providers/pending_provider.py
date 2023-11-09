"""Abstract class for providers that need to wait for on demand calculations to complete."""

from abc import ABC, abstractmethod
from threading import Thread
from datetime import datetime
from math import isnan, isinf

from pandas import DataFrame

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.accessors.study import StudyAccess
from spatialprofilingtoolbox.ondemand.providers.provider import OnDemandProvider
from spatialprofilingtoolbox.workflow.common.export_features import \
    ADIFeatureSpecificationUploader
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class PendingProvider(OnDemandProvider, ABC):
    """Provide precalculated metrics or start, wait, receive, and then provide them."""

    def get_metrics(
        self,
        study: str,
        **kwargs,
    ) -> dict[str, dict[str, float | None] | bool]:
        """Get requested metrics or signal that it's not done calculating yet."""
        logger.debug('Requesting computation.')
        with DBCursor(study=study) as cursor:
            get = ADIFeatureSpecificationUploader.get_data_analysis_study
            measurement_study_name = StudyAccess(cursor).get_study_components(study).measurement
            data_analysis_study = get(measurement_study_name, cursor)
        get_or_create = self.get_or_create_feature_specification
        feature_specification = get_or_create(study, data_analysis_study, **kwargs)
        if self._is_already_computed(study, feature_specification):
            is_pending = False
            logger.debug('Already computed.')
        else:
            is_pending = self._is_already_pending(study, feature_specification)
            if is_pending:
                logger.debug('Already pending.')
            else:
                logger.debug('Not already pending.')
            if not is_pending:
                logger.debug('Starting background task.')
                self._fork_computation_task(study, feature_specification)
                self._set_pending_computation(study, feature_specification)
                logger.debug('Background task just started, is pending.')
                is_pending = True
        return self._query_for_computed_feature_values(
            study,
            feature_specification,
            still_pending=is_pending,
        )

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

    @classmethod
    def create_feature_specification(cls,
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
        logger.debug('Number of values possible to be computed: %s', number)
        return number

    @staticmethod
    def _get_expected_domain_for_computed_values(
        study: str,
        feature_specification: str,
    ) -> list[str]:
        with DBCursor(study=study) as cursor:
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
    def _get_actual_number_of_computed_values(study: str, feature_specification: str) -> int:
        with DBCursor(study=study) as cursor:
            cursor.execute('''
            SELECT COUNT(*) FROM quantitative_feature_value qfv
            WHERE qfv.feature=%s
            ;
            ''', (feature_specification,))
            rows = cursor.fetchall()
            logger.debug('Actual number computed: %s', rows[0][0])
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

    def _fork_computation_task(self, study:str, feature_specification: str) -> None:
        background_thread = Thread(
            target=self.have_feature_computed,
            args=(study, feature_specification,)
        )
        background_thread.start()

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

    def reset_timeout(self, study: str, feature_specification: str) -> None:
        now_seconds = datetime.now().timestamp()
        args = (study, feature_specification)
        self.timeouts[args] = now_seconds

    def check_timeout(self, study: str, feature_specification: str) -> bool:
        now_seconds = datetime.now().timestamp()
        args = (study, feature_specification)
        if args in self.timeouts:
            difference = now_seconds - self.timeouts[args]
            if difference > self.timeout:
                logger.debug('Ondemand timeout %s exceeded.', self.timeout)
                del self.timeouts[args]
                return True
        else:
            self.timeouts[args] = now_seconds
        return False

    @abstractmethod
    def have_feature_computed(self, study: str, feature_specification: str) -> None:
        """Compute the feature and add it to the database."""
        raise NotImplementedError("For subclasses to implement.")

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
    def get_sample_identifiers(cls, study: str, feature_specification: str) -> list[str]:
        return cls._get_expected_domain_for_computed_values(study, feature_specification)

    def get_cells(self, sample_identifier: str, data_analysis_study: str) -> DataFrame:
        return self.data_arrays[data_analysis_study][sample_identifier]

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
