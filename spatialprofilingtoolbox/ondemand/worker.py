"""Handler for requests for on demand calculations."""

from traceback import print_exception

from psycopg import Connection as PsycopgConnection

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import DBConnection
from spatialprofilingtoolbox.ondemand.providers.pending_provider import PendingProvider
from spatialprofilingtoolbox.ondemand.providers.squidpy_provider import SquidpyProvider
from spatialprofilingtoolbox.ondemand.providers.counts_provider import CountsProvider
from spatialprofilingtoolbox.ondemand.providers.proximity_provider import ProximityProvider

from spatialprofilingtoolbox.db.describe_features import get_handle
from spatialprofilingtoolbox.ondemand.job_reference import ComputationJobReference
from spatialprofilingtoolbox.ondemand.scheduler import MetricComputationScheduler
from spatialprofilingtoolbox.ondemand.timeout import create_timeout_handler
from spatialprofilingtoolbox.ondemand.timeout import SPTTimeoutError
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
Job = ComputationJobReference

logger = colorized_logger(__name__)


class OnDemandWorker:
    """Worker that computes one feature value at a time."""
    queue: MetricComputationScheduler
    connection: PsycopgConnection

    def __init__(self):
        self.queue = MetricComputationScheduler(None)

    def start(self) -> None:
        self._listen_for_queue_activity()

    def _listen_for_queue_activity(self) -> None:
        with DBConnection() as connection:
            self.connection = connection
            self.connection._set_autocommit(True)
            self.connection.execute('LISTEN new_items_in_queue ;')
            logger.info('Listening on new_items_in_queue channel.')
            self.notifications = self.connection.notifies()
            while True:
                self._wait_for_queue_activity_on_connection()
                self._work_until_complete()

    def _wait_for_queue_activity_on_connection(self) -> None:
        for _ in self.notifications:
            logger.info('Received notice of new items in the job queue.')
            break

    def _work_until_complete(self) -> None:
        completed = True
        completed_pids = []
        while completed:
            completed, pid = self._one_job()
            if completed:
                completed_pids.append(str(pid))
        logger.info(f'Finished jobs {" ".join(completed_pids)}.')

    def _one_job(self) -> tuple[bool, int]:
        pid = self.connection.info.backend_pid
        job = self.queue.pop_uncomputed()
        if job is None:
            return (False, pid)
        logger.info(f'{pid} doing job {job.feature_specification} {job.sample}.')
        self._compute(job)
        self._notify_complete(job)
        return (True, pid)

    def _no_value_wrapup(self, job) -> None:
        provider = self._get_provider(job)
        provider._warn_no_value()
        provider._insert_null()

    def _compute(self, job: Job) -> None:
        provider = self._get_provider(job)
        generic_handler = create_timeout_handler(
            lambda *arg: self._no_value_wrapup(job),
            timeout_seconds=150,
        )
        try:
            provider.compute()
        except SPTTimeoutError:
            pass
        except Exception as error:
            logger.error(error)
            print_exception(type(error), error, error.__traceback__)
        finally:
            generic_handler.disalarm()

    def _notify_complete(self, job: Job) -> None:
        self.connection.execute('NOTIFY one_job_complete ;')

    def _get_provider(self, job: Job) -> PendingProvider:
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

    def _retrieve_derivation_method(self, job: Job) -> str:
        with DBCursor(study=job.study) as cursor:
            query = 'SELECT derivation_method FROM feature_specification WHERE identifier=%s ;'
            cursor.execute(query, (str(job.feature_specification),))
            return tuple(cursor.fetchall())[0][0]
