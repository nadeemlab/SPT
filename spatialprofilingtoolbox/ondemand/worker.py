"""Handler for requests for on demand calculations."""

from typing import cast
from time import sleep

from psycopg import Connection as PsycopgConnection

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import DBConnection
from spatialprofilingtoolbox.ondemand.providers.provider import OnDemandProvider
from spatialprofilingtoolbox.ondemand.providers.squidpy_provider import SquidpyProvider
from spatialprofilingtoolbox.ondemand.providers.counts_provider import CountsProvider
from spatialprofilingtoolbox.ondemand.providers.proximity_provider import ProximityProvider

from spatialprofilingtoolbox.db.describe_features import get_handle
from spatialprofilingtoolbox.ondemand.job_reference import ComputationJobReference
from spatialprofilingtoolbox.ondemand.scheduler import MetricComputationScheduler
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria

logger = colorized_logger(__name__)


class OnDemandWorker:
    """Worker that computes one feature value at a time."""
    queue: MetricComputationScheduler

    def __init__(self):
        self.queue = MetricComputationScheduler(None)

    def start(self) -> None:
        self._listen_for_queue_activity()

    def _listen_for_queue_activity(self) -> None:
        while True:
            with DBConnection() as connection:
                self._wait_for_queue_activity_on(connection)
                self._work_until_complete()

    def _wait_for_queue_activity_on(self, connection: PsycopgConnection) -> None:
        connection.execute('LISTEN queue_activity ;')
        logger.info('Listening on queue_activity channel.')
        notifications = connection.notifies()
        for notification in notifications:
            if notification.payload == 'new items':
                notifications.close()
                logger.info('Received notice of new items in job queue.')
                break

    def _work_until_complete(self) -> None:
        completed = True
        count = 0
        while completed:
            completed = self._one_job()
            if completed:
                count += 1
        logger.info(f'Finished {count} jobs.')

    def _one_job(self) -> bool:
        job = self.queue.pop_uncomputed()
        if job is None:
            return False
        message = f'Working on job ({job.study}, {job.feature_specification}, {job.sample})'
        logger.info(message)
        self._compute(job)
        return True

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
        return providers[get_handle(derivation_method)](job)  # type: ignore

    def _retrieve_derivation_method(self, job: ComputationJobReference) -> str:
        with DBCursor(study=job.study) as cursor:
            query = 'SELECT derivation_method FROM feature_specification WHERE identifier=%s ;'
            cursor.execute(query, (str(job.feature_specification),))
            return tuple(cursor.fetchall())[0][0]
