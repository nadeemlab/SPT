"""TCP client for on demand metrics service."""

import re
import json
import socket
import os

from asyncio import sleep as asyncio_sleep

from spatialprofilingtoolbox.ondemand.providers.counts_provider import CountsProvider
from spatialprofilingtoolbox.ondemand.providers.proximity_provider import ProximityProvider
from spatialprofilingtoolbox.ondemand.providers.squidpy_provider import SquidpyProvider
from spatialprofilingtoolbox.ondemand.scheduler import MetricComputationScheduler
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import (
    PhenotypeCriteria,
    PhenotypeCount,
    PhenotypeCounts,
    CompositePhenotype,
    UnivariateMetricsComputationResult,
    CellData,
)
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def _fancy_round(ratio: float) -> float:
    return 100 * round(ratio * 10000)/10000


class OnDemandRequester:
    """Entry point for requesting computation by the on-demand service."""

    @staticmethod
    async def get_counts_by_specimen(
        positives: list[str],
        negatives: list[str],
        study_name: str,
        number_cells: int,
        cells_selected: set[int],
    ) -> PhenotypeCounts:
        phenotype = PhenotypeCriteria(
            positive_markers=tuple(positives), negative_markers=tuple(negatives),
        )
        selected = tuple(sorted(list(cells_selected)))
        get = CountsProvider.get_metrics_or_schedule
        while True:
            counts = get(
                study_name,
                phenotype=phenotype,
                cells_selected=selected,
            )
            counts_all = get(
                study_name,
                phenotype=PhenotypeCriteria(positive_markers=(), negative_markers=()),
                cells_selected=selected,
            )
            if not counts.is_pending and not counts_all.is_pending:
                break
            await asyncio_sleep(3)
        combined_keys = sorted(list(set(list(counts.values.keys()) + list(counts_all.values.keys()))))
        return PhenotypeCounts(
            counts=tuple(
                PhenotypeCount(
                    specimen = sample,
                    count = counts.values[sample],
                    percentage = _fancy_round(counts.values[sample] / counts_all.values[sample])
                    if ((counts.values[sample] is not None) and (counts_all.values[sample] not in {0, None})) else None,
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

    @staticmethod
    def get_proximity_metrics(
        study: str,
        radius: float,
        signature: tuple[list[str], list[str], list[str], list[str]]
    ) -> UnivariateMetricsComputationResult:
        phenotype1 = PhenotypeCriteria(
            positive_markers=tuple(signature[0]), negative_markgers=tuple(signature[1]),
        )
        phenotype2 = PhenotypeCriteria(
            positive_markers=tuple(signature[2]), negative_markgers=tuple(signature[3]),
        )
        get = ProximityProvider.get_metrics_or_schedule
        return get(study, phenotype1=phenotype1, phenotype2=phenotype2, radius=radius)

    @staticmethod
    def get_squidpy_metrics(
        study: str,
        signature: list[list[str]],
        feature_class: str,
        radius: float | None = None,
    ) -> UnivariateMetricsComputationResult:
        """Get spatial proximity statistics between phenotype clusters as calculated by Squidpy."""
        if not len(signature) in {2, 4}:
            message = f'Expected 2 or 4 channel lists (1 or 2 phenotypes) but got {len(signature)}.'
            raise ValueError(message)
        if feature_class == 'co-occurrence':
            if radius is None:
                raise ValueError('You must supply a radius value.')
        phenotypes = []
        for i in range(int(len(signature)/2)):
            phenotypes.append(
                PhenotypeCriteria(
                    positive_markers = tuple(signature[2*i]),
                    negative_markers = tuple(signature[2*i + 1]),
                )
            )
        get = SquidpyProvider.get_metrics_or_schedule
        return get(study, feature_class=feature_class, phenotypes=phenotypes, radius=radius)
