"""Handler for requests for on demand calculations."""

from typing import cast
from time import sleep

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.ondemand.providers.provider import OnDemandProvider
from spatialprofilingtoolbox.ondemand.providers.squidpy_provider import SquidpyProvider
from spatialprofilingtoolbox.ondemand.providers.counts_provider import CountsProvider
from spatialprofilingtoolbox.ondemand.providers.proximity_provider import ProximityProvider

from spatialprofilingtoolbox.db.describe_features import get_handle
from spatialprofilingtoolbox.ondemand.scheduler import ComputationJobReference
from spatialprofilingtoolbox.ondemand.scheduler import MetricComputationScheduler
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria

logger = colorized_logger(__name__)

DEFAULT_POLL_PERIOD_SECONDS = 5


class OnDemandWorker:
    """Worker that computes one feature value at a time."""
    queue: MetricComputationScheduler

    def __init__(self):
        self.queue = MetricComputationScheduler(None)

    def start(self) -> None:
        self._poll_for_work()

    def _poll_for_work(self) -> None:
        while True:
            completed = self._one_job()
            if not completed:
                sleep(DEFAULT_POLL_PERIOD_SECONDS)

    def _one_job(self) -> bool:
        job = self.queue.pop_uncomputed()
        if job is not None:
            message = f'Working on job ({job.study}, {job.feature_specification}, {job.sample})'
            logger.info(message)
            self._compute(job)
            return True
        return False

    def _compute(self, job: ComputationJobReference) -> None:
        provider = self._get_provider(job)
        provider.compute()

    def _get_provider(self, job: ComputationJobReference) -> OnDemandProvider:
        derivation_method = self._retrieve_derivation_method(job)
        providers = {
            'spatial autocorrelation': SquidpyProvider,
            'neighborhood enrichment': SquidpyProvider,
            'co-occurrence': SquidpyProvider,
            'ripley': SquidpyProvider,
            'population fractions': CountsProvider,
            'proximity': ProximityProvider,
        }
        return providers[get_handle(derivation_method)](job)

    def _retrieve_derivation_method(self, job: ComputationJobReference) -> str:
        with DBCursor(study=job.study) as cursor:
            query = 'SELECT derivation_method FROM feature_specification WHERE identifier=%s ;'
            cursor.execute(query, (str(job.feature_specification),))
            return tuple(cursor.fetchall())[0][0]
