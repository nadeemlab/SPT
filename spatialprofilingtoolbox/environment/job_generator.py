import os
from os.path import join, exists, abspath
import re
import hashlib
from enum import Enum, auto
import sqlite3

import pandas as pd

from .settings_wrappers import JobsPaths, RuntimeEnvironmentSettings, DatasetSettings
from .pipeline_design import PipelineDesign
from .log_formats import colorized_logger

logger = colorized_logger(__name__)


class JobActivity(Enum):
    """
    Codes for job states, as they will appear in job metadata tables.
    """
    NOT_STARTED = auto()
    RUNNING = auto()
    COMPLETE = auto()
    FAILED = auto()


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
        outcomes_file: str=None,
        excluded_hostname: str='NO_EXCLUDED_HOSTNAME',
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
            outcomes_file (str):
                A tabular text file assigning outcome values (in second column) to
                sample identifiers (first column).
            excluded_hostname (str):
                The name of a host to avoid deploying to (e.g. a control node).
        """
        outcomes_file = outcomes_file if outcomes_file != 'None' else None
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
            outcomes_file,
        )

        self.file_metadata = pd.read_csv(self.dataset_settings.file_manifest_file, sep='\t')
        self.pipeline_design = PipelineDesign()
        self.excluded_hostname = excluded_hostname

    def generate(self):
        """
        This is the main exposed API call.

        It generates jobs involving input files and write to the jobs subdirectory. Also
        writes scripts that schedule the jobs.
        """
        self.initialize_job_activity_table()
        self.populate_file_metadata_table()
        self.gather_input_info()
        self.clean_directory_area()
        self.generate_all_jobs()
        self.generate_scheduler_scripts()

    def initialize_job_activity_table(self):
        """
        Creates a `job_activity` table with which jobs may advertise their running
        states to each other.
        """
        connection = sqlite3.connect(self.pipeline_design.get_database_uri())
        cursor = connection.cursor()
        cursor.execute('DROP TABLE IF EXISTS job_activity ;')
        header = ['Job_status']
        cmd = ' '.join([
            'CREATE TABLE',
            'job_activity',
            '( ',
            'id INTEGER PRIMARY KEY AUTOINCREMENT, ',
            ', '.join([re.sub(' ', '_', key) + ' TEXT' for key in header]),
            ' );',
        ])
        cursor.execute(cmd)
        cursor.close()
        connection.commit()
        connection.close()

    def populate_file_metadata_table(self):
        """
        Pulls in file metadata from the file manifest file into the database accessible
        to all jobs.
        """
        header = JobGenerator.cached_file_metadata_header

        connection = sqlite3.connect(self.pipeline_design.get_database_uri())
        cursor = connection.cursor()
        cursor.execute('DROP TABLE IF EXISTS file_metadata ;')
        cmd = ' '.join([
            'CREATE TABLE',
            'file_metadata',
            '(',
            'id INTEGER PRIMARY KEY AUTOINCREMENT,',
            ' , '.join([
                column_name + ' ' + data_type_descriptor for column_name, data_type_descriptor in header
            ]),
            ');',
        ])
        cursor.execute(cmd)

        file_metadata = self.file_metadata
        for i, row in file_metadata.iterrows():
            file_id = row['File ID']
            filename = row['File name']
            sample_id = row['Sample ID']
            sha256 = row['Checksum']
            datatype = row['Data type']
            if row['Checksum scheme'] != 'SHA256':
                logger.error('Checksum for file with id "%s" is not SHA256. Cannot check file integrity.', file_id)
            if not re.match('^[a-f0-9]{64}$', sha256):
                logger.error('SHA256 checksum %s for file with id "%s" is malformed.', sha256, file_id)
            values_str = ', '.join([
                '"' + file_id + '"',
                '"' + sample_id + '"',
                '"' + sha256 + '"',
                '"' + filename + '"',
                '"' + datatype + '"',
            ])
            cmd = ' '.join([
                'INSERT INTO',
                'file_metadata',
                '( ' + ', '.join([column_name for column_name, dtype in header]) + ' )',
                'VALUES',
                '( ' + values_str + ' );'
            ])
            cursor.execute(cmd)

        cursor.close()
        connection.commit()
        connection.close()

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
        A utility function to make an empty directory at a given location (deleting all
        of its contents if it already exists).

        Args:
            path (str):
                A directory path.
        """
        if not exists(path):
            os.mkdir(path)
        else:
            files = os.listdir(path)
            for file in files:
                os.remove(join(path, file))

    def register_job_existence(self):
        """
        To be called by the implementation JobGenerator to request minting of a new job
        index.
        """
        keys = '( Job_status )'
        values = '( ' + '"' + JobActivity.NOT_STARTED.name + '"' + ' )'

        connection = sqlite3.connect(self.pipeline_design.get_database_uri())
        cursor = connection.cursor()
        cmd = 'INSERT INTO job_activity ' + keys + ' VALUES ' + values + ' ;'
        cursor.execute(cmd)

        cmd = 'SELECT last_insert_rowid()'
        result = cursor.execute(cmd)
        index = int(result.fetchall()[0][0])

        cursor.close()
        connection.commit()
        connection.close()

        return index

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
