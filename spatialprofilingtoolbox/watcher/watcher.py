"""Watch for failed jobs and handle the insertion of default results."""
from typing import cast

from psycopg import Connection as PsycopgConnection

from spatialprofilingtoolbox.db.database_connection import DBConnection
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.ondemand.job_reference import ComputationJobReference
from spatialprofilingtoolbox.ondemand.job_reference import CompletedFeature
from spatialprofilingtoolbox.ondemand.job_reference import JobSerialization
from spatialprofilingtoolbox.ondemand.job_reference import parse_notification
from spatialprofilingtoolbox.ondemand.job_reference import create_notify_command
from spatialprofilingtoolbox.ondemand.job_reference import notify_feature_complete
from spatialprofilingtoolbox.workflow.common.export_features import add_feature_value
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
Job = ComputationJobReference

logger = colorized_logger(__name__)


class WorkerWatcher:
    """Watch for failed jobs and handle the insertion of default results."""
    connection: PsycopgConnection
    worker_jobs: dict[Job, int]

    def __init__(self) -> None:
        self.worker_jobs = {}

    def start(self) -> None:
        with DBConnection() as connection:
            connection._set_autocommit(True)
            connection.execute('LISTEN queue_activity ;')
            self.connection = connection
            logger.info('Watching workers.')
            while True:
                self._monitor()

    def _monitor(self) -> None:
        notifications = self.connection.notifies()
        for _notification in notifications:
            notification = parse_notification(_notification)
            channel = notification.channel
            pid = notification.pid
            payload = notification.payload
            check: Job | None = None
            if channel == 'queue pop':
                job = cast(Job, payload)
                self.worker_jobs[job] = pid
                logger.debug(f'{pid} claims to be working on {job.feature_specification} {job.sample}.')
            if channel == 'job complete':
                job = cast(Job, payload)
                self._log_status_of_completion_notice(job, pid)
                job_present = job in self.worker_jobs.keys()
                if job_present:
                    del self.worker_jobs[job]
                check = job
            if channel == 'check for failed jobs':
                self._check_for_failed_jobs()
            self._log_status()
            if check is not None:
                self._check_for_feature_completion(check.study, check.feature_specification)

    def _log_status_of_completion_notice(self, job: ComputationJobReference, pid: int) -> None:
        pid_present = pid in self.worker_jobs.values()
        job_present = job in self.worker_jobs.keys()
        job_str = f'{job.feature_specification}, {job.sample}'
        if pid_present:
            if job_present:
                del self.worker_jobs[job]
                logger.debug(f'{pid} claims to have completed {job_str}.')
            else:
                logger.warning(f'{pid} was not working on job {job_str}.')
        else:
            if job_present:
                _pid = self.worker_jobs[job]
                message = f'The job {job_str} was picked up by {_pid}, not {pid}.'
                logger.warning(message)
            else:
                ignored = 'Completion notice ignored.'
                message = f'Neither worker {pid} nor job {job_str} are recorded. {ignored}'
                logger.warning(message)

    def _log_status(self) -> None:
        pids = sorted(list(self.worker_jobs.values()))
        abridged = pids[0:min(5, len(pids))]
        display_pids = ' '.join(map(str, abridged))
        if len(pids) > len(abridged):
            display_pids = display_pids + ' ...'
        cw = len(self.worker_jobs)
        cj = len(self.worker_jobs.values())
        r = self._get_queue_size()
        logger.info(f'Recorded {cw} workers ({display_pids}) actively working on {cj} jobs ({r} remaining).')

    def _get_queue_size(self) -> int:
        count = 0
        for study in self._get_studies():
            with DBCursor(study=study) as cursor:
                queue = 'SELECT COUNT(*) FROM quantitative_feature_value_queue ;'
                cursor.execute(queue)
                count += tuple(cursor.fetchall())[0][0]
        return count

    def _get_studies(self) -> tuple[str, ...]:
        with DBCursor() as cursor:
            cursor.execute('SELECT study FROM study_lookup ;')
            return tuple(map(lambda row: row[0], cursor.fetchall()))

    def _check_for_feature_completion(self, study: str, feature: int) -> None:
        with DBCursor(study=study) as cursor:
            queue = 'SELECT COUNT(*) FROM quantitative_feature_value_queue WHERE feature=%s ;'
            cursor.execute(queue, (str(feature),))
            count = tuple(cursor.fetchall())[0][0]
        if count > 0:
            return
        def match(worker_job: tuple[Job, int]) -> bool:
            job = worker_job[0]
            return job.feature_specification == feature and job.study == study
        number_active = len(tuple(filter(match, self.worker_jobs.items())))
        if number_active > 0:
            return
        logger.debug(f'Feature {feature} jobs no longer in queue or active/running.')
        notify_feature_complete(study, feature, self.connection)

    def _check_for_failed_jobs(self) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute('SELECT pid FROM pg_stat_activity ;')
            pids = tuple(map(lambda row: int(row[0]), cursor.fetchall()))
        for pid in set(self.worker_jobs.values()).difference(pids):
            self._assume_dead(pid)

    def _assume_dead(self, pid: int) -> None:
        jobs = tuple(map(
            lambda job_pid: job_pid[0],
            filter(lambda job_pid: job_pid[1] == pid, self.worker_jobs.items(),),
        ))
        for job in jobs:
            _job = JobSerialization.to_string(job)
            message = f'Completion of job "{_job}" by {pid} inferred, direct notice absent.'
            logger.warning(message)
        for job in jobs:
            del self.worker_jobs[job]
            if self._no_value(job):
                self._warn_dead_job(job)

    def _no_value(self, job: Job) -> bool:
        with DBCursor(study=job.study) as cursor:
            query = '''
            SELECT COUNT(*) FROM quantitative_feature_value WHERE feature=%s AND subject=%s ;
            '''
            cursor.execute(query, (str(job.feature_specification), job.sample))
            count = len(tuple(cursor.fetchall()))
        return count == 0

    def _warn_dead_job(self, job: Job) -> None:
        specification = str(job.feature_specification)
        study = job.study
        sample = job.sample
        message = f'Worker for feature {specification} ({sample}, {study}) did not write a value before closing its connection.'
        logger.warning(message)
