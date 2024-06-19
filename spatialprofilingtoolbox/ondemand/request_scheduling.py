"""Entry point for requesting computation by the on-demand service."""

from typing import cast

from psycopg import Connection as PsycopgConnection

from spatialprofilingtoolbox.ondemand.job_reference import parse_notification
from spatialprofilingtoolbox.ondemand.job_reference import create_notify_command
from spatialprofilingtoolbox.ondemand.job_reference import JobSerialization
from spatialprofilingtoolbox.ondemand.job_reference import CompletedFeature
from spatialprofilingtoolbox.db.database_connection import DBConnection
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.ondemand.providers.counts_provider import CountsProvider
from spatialprofilingtoolbox.ondemand.providers.proximity_provider import ProximityProvider
from spatialprofilingtoolbox.ondemand.providers.squidpy_provider import SquidpyProvider
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import (
    PhenotypeCriteria,
    PhenotypeCount,
    PhenotypeCounts,
    CompositePhenotype,
    UnivariateMetricsComputationResult,
)
from spatialprofilingtoolbox.ondemand.relevant_specimens import relevant_specimens_query
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
Metrics1D = UnivariateMetricsComputationResult

logger = colorized_logger(__name__)


def _fancy_division(numerator: float | None, denominator: float | None) -> float:
    if numerator is None or denominator is None:
        return 0
    if denominator == 0 or numerator == 0:
        return 0
    ratio = numerator / denominator
    return 100 * round(ratio * 10000)/10000


def _nonempty(string: str) -> bool:
    return string != ''


class OnDemandRequester:
    """Entry point for requesting computation by the on-demand service."""

    @staticmethod
    def get_counts_by_specimen(
        positives: tuple[str, ...],
        negatives: tuple[str, ...],
        study_name: str,
        number_cells: int,
        cells_selected: set[int],
    ) -> PhenotypeCounts:
        phenotype = PhenotypeCriteria(
            positive_markers=tuple(filter(_nonempty, positives)),
            negative_markers=tuple(filter(_nonempty, negatives)),
        )
        selected = tuple(sorted(list(cells_selected))) if cells_selected is not None else ()
        feature1, counts, counts_all = OnDemandRequester._counts(study_name, phenotype, selected)
        combined_keys = sorted(list(set(counts.values.keys()).intersection(counts_all.values.keys())))
        missing_numerator = set(counts.values.keys()).difference(combined_keys)
        if len(missing_numerator) > 0:
            logger.warning(f'In forming population fractions, some samples were missing from numerator: {missing_numerator}')
        missing_denominator = set(counts_all.values.keys()).difference(combined_keys)
        if len(missing_denominator) > 0:
            logger.warning(f'In forming population fractions, some samples were missing from denominator: {missing_denominator}')
        expected = CountsProvider._get_expected_samples(study_name, feature1)
        additional = set(expected).difference(combined_keys)
        return PhenotypeCounts(
            counts=tuple([
                PhenotypeCount(
                    specimen = sample,
                    count = int(cast(float, counts.values[sample])) if counts.values[sample] is not None else 0,
                    percentage = _fancy_division(counts.values[sample], counts_all.values[sample]),
                )
                for sample in combined_keys
            ] + [PhenotypeCount(specimen=sample, count=0, percentage=0) for sample in additional]),
            phenotype=CompositePhenotype(
                name='',
                identifier='',
                criteria=phenotype,
            ),
            number_cells_in_study=number_cells,
        )

    @classmethod
    def _counts(
        cls, study_name: str, phenotype: PhenotypeCriteria, selected: tuple[int, ...],
    ) -> tuple[str, Metrics1D, Metrics1D]:
        get = CountsProvider.get_metrics_or_schedule

        def get_results() -> tuple[Metrics1D, str]:
            counts, feature1 = get(
                study_name,
                phenotype=phenotype,
                cells_selected=selected,
            )
            return (counts, feature1)

        with DBConnection() as connection:
            connection._set_autocommit(True)
            connection.execute('LISTEN queue_activity ;')
            counts, feature1 = get_results()
            while cls._feature_is_missing_values(study_name, feature1):
                cls._wait_for_wrapup_activity(connection, feature1)
                counts, _ =  get_results()
                if not counts.is_pending:
                    break

        def get_results2() -> tuple[Metrics1D, str]:
            counts_all, feature2 = get(
                study_name,
                phenotype=PhenotypeCriteria(positive_markers=(), negative_markers=()),
            )
            return (counts_all, feature2)

        with DBConnection() as connection:
            connection._set_autocommit(True)
            connection.execute('LISTEN queue_activity ;')
            counts_all, feature2 = get_results2()
            while cls._feature_is_missing_values(study_name, feature2):
                cls._wait_for_wrapup_activity(connection, feature2)
                counts_all, _ =  get_results2()
                if not counts_all.is_pending:
                    break

        cls._request_check_for_failed_jobs()
        return (feature1, counts, counts_all)

    @classmethod
    def _request_check_for_failed_jobs(cls) -> None:
        notify = create_notify_command('check for failed jobs', '')
        with DBConnection() as connection:
            connection._set_autocommit(True)
            connection.execute(notify)

    @classmethod
    def _wait_for_wrapup_activity(cls, connection: PsycopgConnection, feature: str) -> None:
        logger.debug(f'Waiting for signal that feature {feature} may be ready.')
        notifications = connection.notifies()
        for _notification in notifications:
            notification = parse_notification(_notification)
            channel = notification.channel
            payload = notification.payload
            if channel == 'feature computation jobs complete':
                payload = cast(CompletedFeature, payload)
                fs = payload.feature_specification
                if fs != int(feature):
                    logger.warning(f'Waiting for {feature}, not {fs} (which may be complete).')
                    continue
                logger.debug(f'Feature {fs} computation jobs no longer present in queue.')
                notifications.close()
                break

    @classmethod
    def _feature_is_missing_values(cls, study: str, feature: str) -> bool:
        missing = cls._get_missing_samples(study, feature)

        if len(missing) == 0:
            logger.debug(f'Feature {feature} is NOT missing values.')

        return len(missing) > 0

    @classmethod
    def _get_expected_samples(cls, study: str, feature_specification: str) -> tuple[str, ...]:
        with DBCursor(study=study) as cursor:
            query = relevant_specimens_query() % f"'{feature_specification}'"
            cursor.execute(query)
            return tuple(map(lambda row: row[0], cursor.fetchall()))

    @classmethod
    def _get_missing_samples(cls, study: str, feature_specification: str) -> tuple[str, ...]:
        expected = cls._get_expected_samples(study, feature_specification)
        with DBCursor(study=study) as cursor:
            query = 'SELECT subject FROM quantitative_feature_value WHERE feature=%s ;'
            cursor.execute(query, (feature_specification,))
            present = tuple(map(lambda row: row[0], cursor.fetchall()))
        return tuple(sorted(list(set(expected).difference(present))))

    @classmethod
    def get_proximity_metrics(
        cls,
        study: str,
        radius: float,
        _signature: tuple[list[str], list[str], list[str], list[str]]
    ) -> Metrics1D:
        signature = tuple(map(lambda l: tuple(filter(_nonempty, l)), _signature))
        phenotype1 = PhenotypeCriteria(
            positive_markers=signature[0], negative_markers=signature[1],
        )
        phenotype2 = PhenotypeCriteria(
            positive_markers=signature[2], negative_markers=signature[3],
        )
        get = ProximityProvider.get_metrics_or_schedule
        result, _ = get(study, phenotype1=phenotype1, phenotype2=phenotype2, radius=radius)
        return result

    @classmethod
    def get_squidpy_metrics(
        cls,
        study: str,
        _signature: list[list[str]],
        feature_class: str,
        radius: float | None = None,
    ) -> Metrics1D:
        """Get spatial proximity statistics between phenotype clusters as calculated by Squidpy."""
        if not len(_signature) in {2, 4}:
            message = f'Expected 2 or 4 channel lists (1 or 2 phenotypes) but got {len(_signature)}.'
            raise ValueError(message)
        signature = tuple(map(lambda l: tuple(filter(_nonempty, l)), _signature))
        if feature_class == 'co-occurrence':
            if radius is None:
                raise ValueError('You must supply a radius value.')
        phenotypes = []
        for i in range(int(len(signature)/2)):
            phenotypes.append(
                PhenotypeCriteria(
                    positive_markers = signature[2*i],
                    negative_markers = signature[2*i + 1],
                )
            )
        get = SquidpyProvider.get_metrics_or_schedule
        result, _ = get(study, feature_class=feature_class, phenotypes=phenotypes, radius=radius)
        return result
