"""Handler for requests for on demand calculations."""

from os import environ as os_environ
from typing import cast
from traceback import print_exception
from time import time as time_time

from psycopg import Connection as PsycopgConnection

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import DBConnection
from spatialprofilingtoolbox.ondemand.computers.generic_job_computer import GenericJobComputer
from spatialprofilingtoolbox.ondemand.computers.counts_computer import CountsComputer
from spatialprofilingtoolbox.ondemand.computers.proximity_computer import ProximityComputer
from spatialprofilingtoolbox.ondemand.computers.squidpy_computer import SquidpyComputer
from spatialprofilingtoolbox.ondemand.cell_data_cache import CellDataCache

from spatialprofilingtoolbox.db.describe_features import get_handle
from spatialprofilingtoolbox.ondemand.job_reference import ComputationJobReference
from spatialprofilingtoolbox.ondemand.metrics_job_queue_popper import MetricsJobQueuePopper
from spatialprofilingtoolbox.ondemand.timeout import create_timeout_handler
from spatialprofilingtoolbox.ondemand.timeout import SPTTimeoutError
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
Job = ComputationJobReference

logger = colorized_logger(__name__)


class OnDemandWorker:
    """Worker that computes one feature value at a time."""
    connection: PsycopgConnection
    work_start_time_seconds: float | None
    DEFAULT_JOB_COMPUTATION_TIMEOUT_SECONDS: int = 150
    cache: CellDataCache

    def __init__(self):
        self.work_start_time_seconds = None
        self.cache = CellDataCache()

    def start(self) -> None:
        with DBConnection() as connection:
            self.connection = connection
            self.connection._set_autocommit(True)
            logger.info('Initial search (and pop) over job queue.')
            self._work_until_complete()
            self._wait_work_loop()

    def _wait_work_loop(self) -> None:
        self.connection.execute('LISTEN new_items_in_queue ;')
        while True:
            self._wait_for_queue_activity_on_connection()
            self._work_until_complete()

    def _wait_for_queue_activity_on_connection(self) -> None:
        timeout = 3
        notifications = self.connection.notifies(timeout=timeout)
        for _ in notifications:
            break
        logger.debug

    def _work_until_complete(self) -> None:
        completed = True
        completed_jobs = []
        self.work_start_time_seconds = time_time()
        while completed:
            completed, job = self._one_job()
            if completed and (job is not None):
                completed_jobs.append(job)
                reported_on_jobs_already = self._report_on_completed_jobs(completed_jobs)
                if reported_on_jobs_already:
                    completed_jobs = []
        self._report_on_completed_jobs(completed_jobs, time_limit_seconds=None)

    def _report_on_completed_jobs(
        self,
        completed_jobs: list[Job],
        time_limit_seconds: int | None = 60,
    ) -> bool:
        if len(completed_jobs) == 0:
            return False
        delta = time_time() - cast(float, self.work_start_time_seconds)
        delta = int(10 * delta) / 10
        if time_limit_seconds is None:
            prefix = '(reached end of loop over available queue) '
        else:
            prefix = ''
        if time_limit_seconds is None or (delta >= time_limit_seconds):
            abridged = completed_jobs[0:min(3, len(completed_jobs))]
            summary = ', '.join(map(lambda job: f'{job.feature_specification} {job.sample}', abridged))
            if len(completed_jobs) > 3:
                summary = summary + ' ...'
            logger.info(f'{prefix} Finished {len(completed_jobs)} jobs {summary} in {delta} seconds.')
            if time_limit_seconds is None:
                self.work_start_time_seconds = None
            else:
                self.work_start_time_seconds = time_time()
            return True
        return False

    def _one_job(self) -> tuple[bool, ComputationJobReference | None]:
        job = MetricsJobQueuePopper.pop_uncomputed(preference=list(self.cache.cache.keys()))
        if job is None:
            return (False, None)
        self._compute(job)
        self._notify_complete(job)
        return (True, job)

    def _no_value_wrapup(self, job) -> None:
        provider = self._get_provider(job)
        provider._warn_no_value()
        provider._insert_null()
        provider._pop_off_queue()

    def _compute(self, job: Job) -> None:
        provider = self._get_provider(job)
        generic_handler = create_timeout_handler(
            lambda *arg: self._no_value_wrapup(job),
            self._get_job_computation_timeout(),
        )
        try:
            provider.compute()
        except SPTTimeoutError:
            pass
        except Exception as error:
            logger.error(error)
            print_exception(type(error), error, error.__traceback__)
            self._no_value_wrapup(job)
        finally:
            generic_handler.disalarm()

    def _get_job_computation_timeout(self) -> int:
        t = 'JOB_COMPUTATION_TIMEOUT_SECONDS'
        if t in os_environ:
            return int(os_environ[t])
        logger.warning(f'Set {t}. Using default: {self.DEFAULT_JOB_COMPUTATION_TIMEOUT_SECONDS}')
        return self.DEFAULT_JOB_COMPUTATION_TIMEOUT_SECONDS

    def _notify_complete(self, job: Job) -> None:
        with DBConnection() as connection:
            connection.execute('NOTIFY one_job_complete ;')

    def _get_provider(self, job: Job) -> GenericJobComputer:
        derivation_method = self._retrieve_derivation_method(job)
        providers = {
            'spatial autocorrelation': SquidpyComputer,
            'neighborhood enrichment': SquidpyComputer,
            'co-occurrence': SquidpyComputer,
            'ripley': SquidpyComputer,
            'population fractions': CountsComputer,
            'proximity': ProximityComputer,
        }
        return providers[get_handle(derivation_method)](job, self.cache)  # type: ignore

    def _retrieve_derivation_method(self, job: Job) -> str:
        with DBCursor(study=job.study) as cursor:
            query = 'SELECT derivation_method FROM feature_specification WHERE identifier=%s ;'
            cursor.execute(query, (str(job.feature_specification),))
            return tuple(cursor.fetchall())[0][0]
