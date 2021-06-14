import os
from os.path import join, abspath
import functools
from functools import lru_cache
import re
import hashlib

from .job_generator import JobActivity
from .database_context_utility import WaitingDatabaseContextManager
from .pipeline_design import PipelineDesign
from .settings_wrappers import JobsPaths, DatasetSettings
from .log_formats import colorized_logger

logger = colorized_logger(__name__)


class SingleJobAnalyzer:
    """
    An interface for a single job to be executed as part of a batch in a pipeline
    run. It handles the boilerplate of registering the existence and state of the
    job in a shared database. This also includes figuring out whether or not to do
    initialization (in case this job is first to run) or wrap-up (in case this job
    is last to complete).

    It is assumed that one job corresponds to one input file, and that metadata for
    this file can be found in the file_metadata table of the database pointed to by
    get_pipeline_database_uri(). The format of this metadata can be partially
    gleaned from JobGenerator.
    """
    def __init__(self,
        input_path: str=None,
        file_manifest_file: str=None,
        outcomes_file: str=None,
        job_working_directory: str=None,
        jobs_path: str=None,
        logs_path: str=None,
        schedulers_path: str=None,
        output_path: str=None,
        input_file_identifier: str=None,
        job_index: str=None,
    ):
        self.dataset_settings = DatasetSettings(
            input_path,
            file_manifest_file,
            outcomes_file,
        )
        self.jobs_paths = JobsPaths(
            job_working_directory,
            jobs_path,
            logs_path,
            schedulers_path,
            output_path,
        )
        self.input_file_identifier = input_file_identifier
        self.job_index = int(job_index)
        self.pipeline_design = PipelineDesign()

    def get_pipeline_database_uri(self):
        return self.pipeline_design.get_database_uri()

    def _calculate(self):
        pass

    def first_job_started(self):
        pass

    def start_post_jobs_step(self):
        pass

    def calculate(self):
        self.register_activity(JobActivity.RUNNING)
        self._calculate()
        self.register_activity(JobActivity.COMPLETE)

    def retrieve_input_filename(self):
        self.get_input_filename()

    def retrieve_sample_identifier(self):
        self.get_sample_identifier()

    def get_job_index(self):
        return self.job_index

    @lru_cache(maxsize=1)
    def get_input_filename(self):
        where_clause = 'Input_file_identifier="' + self.input_file_identifier + '"'
        cmd = 'SELECT File_basename, SHA256 FROM file_metadata WHERE ' + where_clause + ' ;'
        with WaitingDatabaseContextManager(self.get_pipeline_database_uri()) as m:
            result = m.execute_commit(cmd)
        if len(result) != 1:
            logger.error('Multiple (or no) files with ID %s ?', self.input_file_identifier)
            input_file = None
            sha256 = None
            return
        else:
            row = result[0]
            input_file = row[0]
            expected_sha256 = row[1]
            input_file = abspath(join(self.dataset_settings.input_path, input_file))

            buffer_size = 65536
            sha = hashlib.sha256()
            with open(input_file, 'rb') as f:
                while True:
                    data = f.read(buffer_size)
                    if not data:
                        break
                    sha.update(data)
            sha256 = sha.hexdigest()

            if sha256 != expected_sha256:
                logger.error('File "%s" has wrong SHA256 hash.', self.input_file_identifier)
            return input_file

    @lru_cache(maxsize=1)
    def get_sample_identifier(self):
        where_clause = 'Input_file_identifier="' + self.input_file_identifier + '"'
        cmd = 'SELECT Sample_ID FROM file_metadata WHERE ' + where_clause + ' ;'
        with WaitingDatabaseContextManager(self.get_pipeline_database_uri()) as m:
            result = m.execute_commit(cmd)
        if len(result) != 1:
            logger.error('Multiple files with ID %s ?', self.input_file_identifier)
            sample_identifier = None
        else:
            row = result[0]
            sample_identifier = row[0]
        return sample_identifier

    def register_activity(self, state):
        update_cmd = 'UPDATE job_activity SET Job_status ="' + state.name + '" WHERE id = ' + str(self.get_job_index()) + ' ;'

        if state == JobActivity.FAILED:
            with WaitingDatabaseContextManager(self.get_pipeline_database_uri()) as m:
                m.execute_commit(update_cmd)
            logger.debug('Job with activity index %s has failed.', self.get_job_index())

        if state == JobActivity.RUNNING:
            job_statuses = {}
            with WaitingDatabaseContextManager(self.get_pipeline_database_uri()) as m:
                m.execute_commit(update_cmd)

            # There is a race-condition-type problem here. Ideally, the above and below would execute on the database at the same time.
            # As things stand here, the first process to run may not realize it is the first process to run because another
            # process has intervened between the time that the given one (1) registered its "running" flag, and (2) queried for all "running" flags.
            #
            # Currently this is not a very important problem, because all examples of first_job_started implementations do no
            # important work (just logging).

            with WaitingDatabaseContextManager(self.get_pipeline_database_uri()) as m:
                result = m.execute_commit('SELECT id, Job_status FROM job_activity ;')
                job_statuses = {item[0] : item[1] for item in result}

            number_not_started = len([status for index, status in job_statuses.items() if JobActivity[status] == JobActivity.NOT_STARTED])
            number_running = len([status for index, status in job_statuses.items() if JobActivity[status] == JobActivity.RUNNING])
            number_complete = len([status for index, status in job_statuses.items() if JobActivity[status] == JobActivity.COMPLETE])
            number_failed = len([status for index, status in job_statuses.items() if JobActivity[status] == JobActivity.FAILED])
            number_total = len(job_statuses)

            if number_running == 1 and number_not_started == number_total - 1:
                self.first_job_started()
            logger.debug('Started job with activity index %s', self.get_job_index())

        if state == JobActivity.COMPLETE:
            job_statuses = {}
            with WaitingDatabaseContextManager(self.get_pipeline_database_uri()) as m:
                result = m.execute_commit('SELECT id, Job_status FROM job_activity ;')
                job_statuses = {item[0] : item[1] for item in result}
            job_statuses = {item[0] : item[1] for item in result}

            with WaitingDatabaseContextManager(self.get_pipeline_database_uri()) as m:
                m.execute_commit(update_cmd)

            number_failed = len([status for index, status in job_statuses.items() if JobActivity[status] == JobActivity.FAILED])
            number_completed = len([status for index, status in job_statuses.items() if JobActivity[status] == JobActivity.COMPLETE])
            number_all = len(job_statuses)
            if number_failed + number_completed == number_all - 1:
                logger.info('No remaining not-started jobs.')
                logger.info('%s jobs failed.', number_failed)
                logger.info('%s jobs completed.', number_completed)
                logger.info('Moving on to integration stage.')
                self.start_post_jobs_step()
