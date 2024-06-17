"""Entry point for requesting computation by the on-demand service."""

from typing import cast

from psycopg import Connection as PsycopgConnection

from spatialprofilingtoolbox.db.database_connection import DBConnection
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
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
Metrics1D = UnivariateMetricsComputationResult

logger = colorized_logger(__name__)


def _fancy_division(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
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
        counts, counts_all = OnDemandRequester._counts(study_name, phenotype, selected)
        combined_keys = sorted(list(set(list(counts.values.keys()) + list(counts_all.values.keys()))))
        return PhenotypeCounts(
            counts=tuple(
                PhenotypeCount(
                    specimen = sample,
                    count = int(cast(float, counts.values[sample])) if counts.values[sample] is not None else None,
                    percentage = _fancy_division(counts.values[sample], counts_all.values[sample]),
                )
                for sample in combined_keys
            ),
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
    ) -> tuple[Metrics1D, Metrics1D]:
        get = CountsProvider.get_metrics_or_schedule
        def get_results() -> tuple[Metrics1D, str, Metrics1D, str]:
            counts, feature1 = get(
                study_name,
                phenotype=phenotype,
                cells_selected=selected,
            )
            counts_all, feature2 = get(
                study_name,
                phenotype=PhenotypeCriteria(positive_markers=(), negative_markers=()),
                cells_selected=selected,
            )
            return (counts, feature1, counts_all, feature2)
        with DBConnection() as connection:
            connection._set_autocommit(True)
            connection.execute('LISTEN queue_failed_jobs_cleared ;')
            _, feature1, _, feature2 = get_results()
            while True:
                cls._wait_for_wrapup_activity(connection, (feature1, feature2))
                counts, _, counts_all, _ =  get_results()
                if not counts.is_pending and not counts_all.is_pending:
                    return (counts, counts_all)

    @classmethod
    def _wait_for_wrapup_activity(cls, connection: PsycopgConnection, features: tuple[str, ...]) -> None:
        logger.info(f'Waiting for signals that whole features {features} may be ready.')
        notifications = connection.notifies()
        for notification in notifications:
            logger.info(f'Received signal that whole features {features} may be ready.')
            notifications.close()
            break

    @staticmethod
    def get_proximity_metrics(
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

    @staticmethod
    def get_squidpy_metrics(
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
