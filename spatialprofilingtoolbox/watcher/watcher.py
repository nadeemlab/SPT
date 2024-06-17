"""Watch for failed jobs and handle the insertion of default results."""

from psycopg import Connection as PsycopgConnection

from spatialprofilingtoolbox.db.database_connection import DBConnection
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.ondemand.job_reference import ComputationJobReference
from spatialprofilingtoolbox.workflow.common.export_features import add_feature_value
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
Job = ComputationJobReference

logger = colorized_logger(__name__)


class WorkerWatcher:
    """Watch for failed jobs and handle the insertion of default results."""
    connection: PsycopgConnection
    worker_jobs: dict[int, Job]

    def __init__(self) -> None:
        self.worker_jobs = {}

    def start(self) -> None:
        with DBConnection() as connection:
            connection._set_autocommit(True)
            connection.execute('LISTEN queue_pop_activity ;')
            connection.execute('LISTEN queue_job_complete ;')
            connection.execute('LISTEN queue_activity ;')
            connection.execute('LISTEN feature_cache_hit ;')
            self.connection = connection
            logger.info('Watching workers.')
            while True:
                self._monitor()

    def _monitor(self) -> None:
        notifications = self.connection.notifies()
        for notification in notifications:
            if notification.channel == 'queue_pop_activity':
                payload = notification.payload.split('\t')
                job = Job(int(payload[0]), payload[1], payload[2])
                pid = notification.pid
                self.worker_jobs[pid] = job
            self._check_for_failed_jobs()
            self._log_status()

    def _check_for_failed_jobs(self) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute('SELECT pid FROM pg_stat_activity ;')
            pids = tuple(map(lambda row: int(row[0]), cursor.fetchall()))
        for pid in set(self.worker_jobs.keys()).difference(pids):
            self._assume_dead(pid)
        self._notify_cleared()

    def _log_status(self) -> None:
        pids = sorted(list(self.worker_jobs.keys()))
        abridged = pids[0:min(5, len(pids))]
        display = ' '.join(map(str, abridged))
        if len(pids) > len(abridged):
            display = display + ' ...'
        logger.info(f'{len(self.worker_jobs)} workers actively working on jobs ({display}).')

    def _notify_cleared(self) -> None:
        self.connection.execute('NOTIFY queue_failed_jobs_cleared ;')

    def _assume_dead(self, pid: int) -> None:
        job = self.worker_jobs[pid]
        del self.worker_jobs[pid]
        if self._no_value(job):
            self._insert_null(job)

    def _no_value(self, job: Job) -> bool:
        with DBCursor(study=job.study) as cursor:
            query = '''
            SELECT COUNT(*) FROM quantitative_feature_value WHERE feature=%s AND subject=%s ;
            '''
            cursor.execute(query, (str(job.feature_specification), job.sample))
            count = len(tuple(cursor.fetchall()))
        return count == 0

    def _insert_null(self, job: Job) -> None:
        specification = str(job.feature_specification)
        study = job.study
        sample = job.sample
        logger.warning(f'Assumed null, feature {specification} ({sample}, {study}).')
        with DBCursor(study=study) as cursor:
            add_feature_value(specification, sample, None, cursor)
