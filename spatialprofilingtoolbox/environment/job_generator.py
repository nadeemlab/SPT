import os
from os.path import join, exists, abspath, isfile
import re
import hashlib
from enum import Enum, auto
import sqlite3

import pandas as pd

from .settings_wrappers import JobsPaths, RuntimeEnvironmentSettings, DatasetSettings
from .log_formats import colorized_logger

logger = colorized_logger(__name__)


class JobGenerator:
    """
    An interface for pipeline job generation. Minimally assumes that the pipeline
    acts on input files listed in a file manifest file, itself in a format
    controlled by a relatively precise schema (distributed with the source code of
    this package).

    The schema has 11 fields for each file and includes hashes.
    """
    cached_file_metadata_header = [
        ('Input_file_identifier', 'TEXT'),
        ('Sample_ID', 'TEXT'),
        ('SHA256', 'CHAR(64)'),
        ('File_basename', 'TEXT'),
        ('Data_type', 'TEXT'),
    ]

    def __init__(self,
        job_working_directory: str='./',
        jobs_path: str='./jobs',
        logs_path: str='./logs',
        schedulers_path: str='./',
        output_path: str='./output/',
        runtime_platform: str=None,
        sif_file: str=None,
        input_path: str=None,
        file_manifest_file: str=None,
        excluded_hostname: str='NO_EXCLUDED_HOSTNAME',
        **kwargs,
    ):
        """
        Args:
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
            runtime_platform (str):
                Currently either 'lsf' or 'local' (i.e. an HPC deployment or a local
                run).
            sif_file (str):
                The Singularity container file providing this package (if applicable).
            input_path (str):
                The directory in which files listed in the file manifest should be
                located.
            file_manifest_file (str):
                The file manifest file, in the format of the specification distributed
                with the source code of this package.
            excluded_hostname (str):
                The name of a host to avoid deploying to (e.g. a control node).
        """
        self.jobs_paths = JobsPaths(
            job_working_directory,
            jobs_path,
            logs_path,
            schedulers_path,
            output_path,
        )
        self.runtime_settings = RuntimeEnvironmentSettings(
            runtime_platform,
            sif_file,
        )
        self.dataset_settings = DatasetSettings(
            input_path,
            file_manifest_file,
        )

        self.file_metadata = pd.read_csv(self.dataset_settings.file_manifest_file, sep='\t')
        self.excluded_hostname = excluded_hostname

    def generate(self):
        """
        This is the main exposed API call.

        It generates jobs involving input files and write to the jobs subdirectory. Also
        writes scripts that schedule the jobs.
        """
        self.gather_input_info()
        self.clean_directory_area()
        self.generate_all_jobs()
        self.generate_scheduler_scripts()

    def clean_directory_area(self):
        """
        Clears the jobs path, logs path, and output path from prior runs.
        """
        self.make_fresh_directory(self.jobs_paths.jobs_path)
        self.make_fresh_directory(self.jobs_paths.logs_path)
        self.make_fresh_directory(self.jobs_paths.output_path)
        for file in os.listdir('./'):
            if re.search('^schedule_.+sh$', file):
                os.remove(file)

    def make_fresh_directory(self, path):
        """
        A utility function to clear/delete all *files* in a given directory.

        :param path: A directory path.
        :type path: str
        """
        if not exists(path):
            os.mkdir(path)
        else:
            files = os.listdir(path)
            for file in files:
                full_path = join(path, file)
                if isfile(full_path):
                    os.remove(full_path)

    def gather_input_info(self):
        """
        Bring into object-local state all information about the input files needed to
        specify the jobs.
        """
        pass

    def generate_all_jobs(self):
        """
        Generate the job script files.
        """
        pass

    def generate_scheduler_scripts(self):
        """
        Generate a shell script or scripts that schedule the jobs.
        """
        pass

    @staticmethod
    def apply_replacements(template, replacements):
        """
        :param template: Input with some template values to be filled in.
        :type template: str

        :param replacements: Mapping from template indicator to replacement strings.
        :type replacements: str

        :return: replaced
        :rtype: str
        """
        for key, value in replacements.items():
            template = re.sub(key, value, template)
        return template
