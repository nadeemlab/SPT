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
    run. It handles some "boilerplate".

    It is generally assumed that one job is associated which exactly one input file (the
    reverse is not assumed). And, moreover, that metadata for this file can be found
    in the file_metadata table of the database pointed to by
    ``get_pipeline_database_uri()``. The format of this metadata can be partially
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
        """
        Args:
            input_path (str):
                The directory in which files listed in the file manifest should be
                located.
            file_manifest_file (str):
                The file manifest file, in the format of the specification distributed
                with the source code of this package.
            outcomes_file (str):
                A tabular text file assigning outcome values (in second column) to
                sample identifiers (first column).
            job_working_directory (str):
                This is the directory in which jobs should run. That is, when the job
                processes query for the current working directory, it should yield this
                directory.
            jobs_path (str):
                The directory in which job script files will be written.
            logs_path (str):
                The directory in which log files will be written.
            schedulers_path (str):
                The directory in which the scripts which scheduler jobs will be written.
            output_path (str):
                The directory in which result tables, images, etc. will be written.
            input_file_identifier (str):
                The identifier, as it appears in the file manifest, for the file
                associated with this job.
            job_index (str):
                The string representation of the integer index of this job in the job
                metadata table.
        """
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
        """
        See ``PipelineDesign.get_database_uri``.
        """
        return self.pipeline_design.get_database_uri()

    def _calculate(self):
        """
        Abstract method, the implementation of which is the core/primary computation to
        be performed by this job.
        """
        pass

    def calculate(self):
        """
        The main calculation of this job, to be called by pipeline orchestration.
        """
        self.register_activity(JobActivity.RUNNING)
        self._calculate()
        self.register_activity(JobActivity.COMPLETE)

    def retrieve_input_filename(self):
        self.get_input_filename()

    def retrieve_sample_identifier(self):
        self.get_sample_identifier()

    def get_job_index(self):
        """
        Returns:
            int:
                The index of this job in the job metadata table.
        """
        return self.job_index

    @lru_cache(maxsize=1)
    def get_input_filename(self):
        """
        See ``get_input_filename_by_identifier``. Applied to this job's specific
        ``input_file_identifier``.
        """
        return self.get_input_filename_by_identifier(self.input_file_identifier)

    def get_input_filename_by_identifier(self, input_file_identifier):
        """
        Uses the file identifier to lookup the name of the associated file in the file
        metadata table, and cache the name of the associated file.

        Args:
            input_file_identifier (str):
                Key to search for in the "File ID" column of the file metadata table.

        Returns:
            str:
                The filename.
        """
        where_clause = 'Input_file_identifier="' + input_file_identifier + '"'
        cmd = 'SELECT File_basename, SHA256 FROM file_metadata WHERE ' + where_clause + ' ;'
        with WaitingDatabaseContextManager(self.get_pipeline_database_uri()) as m:
            result = m.execute_commit(cmd)
        if len(result) != 1:
            logger.error('Multiple (or no) files with ID %s ?', input_file_identifier)
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
                logger.error('File "%s" has wrong SHA256 hash (%s ; expected %s).', input_file_identifier, sha256, expected_sha256)
            return input_file

    @lru_cache(maxsize=1)
    def get_sample_identifier(self):
        """
        Uses the file identifier to lookup and cache the associated sample identifier.
        """
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
        """
        (`To be deprecated`).

        Args:
            state (JobActivity):
                The updated job state to be "advertised".
        """
        if state == JobActivity.RUNNING:
            logger.debug('Started job with activity index %s', self.get_job_index())
        if state == JobActivity.COMPLETE:
            logger.debug('Completed entire job with activity index %s', self.get_job_index())
        if state == JobActivity.FAILED:
            logger.debug('Job failed, job with activity index %s', self.get_job_index())
