"""Entry point for requesting computation by the on-demand service."""

from typing import cast
from typing import Callable

from psycopg import Connection as PsycopgConnection

from spatialprofilingtoolbox.db.database_connection import DBConnection
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.workflow.common.export_features import add_feature_value
from spatialprofilingtoolbox.ondemand.providers.counts_provider import CountsProvider
from spatialprofilingtoolbox.ondemand.providers.proximity_provider import ProximityProvider
from spatialprofilingtoolbox.ondemand.providers.squidpy_provider import SquidpyProvider
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import (
    PhenotypeCriteria,
    PhenotypeCount,
    PhenotypeCounts,
    WrapperPhenotype,
    UnivariateMetricsComputationResult,
)
from spatialprofilingtoolbox.ondemand.feature_computation_timeout import FeatureComputationTimeoutHandler
from spatialprofilingtoolbox.ondemand.timeout import create_timeout_handler
from spatialprofilingtoolbox.ondemand.timeout import SPTTimeoutError
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
Metrics1D = UnivariateMetricsComputationResult

logger = colorized_logger(__name__)


def _fancy_division(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    if numerator == 0:
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
        cells_selected: set[int],
        blocking: bool = True,
    ) -> PhenotypeCounts:
        phenotype = PhenotypeCriteria(
            positive_markers=tuple(filter(_nonempty, positives)),
            negative_markers=tuple(filter(_nonempty, negatives)),
        )
        selected = tuple(sorted(list(cells_selected))) if cells_selected is not None else ()
        feature1, counts, counts_all, pending = OnDemandRequester._counts(study_name, phenotype, selected, blocking)
        combined_keys = sorted(list(set(counts.values.keys()).intersection(counts_all.values.keys())))
        missing_denominator = set(counts.values.keys()).difference(combined_keys)
        if len(missing_denominator) > 0:
            logger.warning(f'In forming population fractions, some samples were missing from denominator: {missing_denominator}')
        expected = CountsProvider._get_expected_samples(study_name, feature1)
        additional = set(expected).difference(combined_keys)
        return PhenotypeCounts(
            counts=tuple([
                PhenotypeCount(
                    specimen = sample,
                    count = int(cast(float, counts.values[sample])) if counts.values[sample] is not None else None,
                    percentage = _fancy_division(counts.values[sample], counts_all.values[sample]),
                )
                for sample in combined_keys
            ] + [PhenotypeCount(specimen=sample, count=None, percentage=None) for sample in additional]),
            phenotype=WrapperPhenotype(
                criteria=phenotype,
            ),
            is_pending=pending,
        )

    @classmethod
    def _counts(
        cls,
        study_name: str,
        phenotype: PhenotypeCriteria,
        selected: tuple[int, ...],
        blocking: bool,
    ) -> tuple[str, Metrics1D, Metrics1D, bool]:
        get = CountsProvider.get_metrics_or_schedule

        def get_results1() -> tuple[Metrics1D, str]:
            counts, feature1 = get(
                study_name,
                phenotype=phenotype,
                cells_selected=selected,
            )
            return (counts, feature1)

        def get_results2() -> tuple[Metrics1D, str]:
            counts_all, feature2 = get(
                study_name,
                phenotype=PhenotypeCriteria(positive_markers=(), negative_markers=()),
                cells_selected=selected,
            )
            return (counts_all, feature2)

        with DBConnection() as connection:
            connection._set_autocommit(True)
            if blocking:
                counts, feature1 = cls._wait_for_wrappedup(connection, get_results1, study_name)
            else:
                counts, feature1 =  get_results1()

            if blocking:
                counts_all, _ = cls._wait_for_wrappedup(connection, get_results2, study_name)
            else:
                counts_all, _ =  get_results2()

        return (feature1, counts, counts_all, counts.is_pending or counts_all.is_pending)

    @classmethod
    def _wait_for_wrappedup(
        cls,
        connection: PsycopgConnection,
        get_results: Callable[[], tuple[Metrics1D, str]],
        study_name: str,
    ):
        counts, feature = get_results()
        if not counts.is_pending:
            logger.debug(f'Feature {feature} already complete.')
            return (counts, feature)
        connection.execute('LISTEN new_items_in_queue ;')
        connection.execute('LISTEN one_job_complete ;')
        notifications = connection.notifies()
        handler = FeatureComputationTimeoutHandler(feature, study_name)
        generic_handler = create_timeout_handler(handler.handle)
        try:
            if not counts.is_pending:
                logger.debug(f'Feature {feature} already complete.')
                return (counts, feature)
            logger.debug(f'Waiting for signal that feature {feature} may be ready, because the result is not ready yet.')
            for notification in notifications:
                _result = get_results()
                if not _result[0].is_pending:
                    logger.debug(f'Closing notification processing, {feature} ready.')
                    notifications.close()
                    return _result
            logger.debug(f'Notification processing completed, giving up on feature {feature}')
            cls._clear_queue_of_feature(study_name, int(feature))
        except SPTTimeoutError:
            pass
        finally:
            generic_handler.disalarm()

    @classmethod
    def _clear_queue_of_feature(cls, study: str, feature: int) -> None:
        with DBCursor(study=study) as cursor:
            query = 'DELETE FROM quantitative_feature_value_queue q WHERE q.feature=%s ;'
            cursor.execute(query, (feature,))
            logger.debug(f'Cleared the job queue for feature {feature} ({study}).')

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
