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
    NOT_STARTED = auto()
    RUNNING = auto()
    COMPLETE = auto()
    FAILED = auto()


class JobGenerator:
    """
    An interface for pipeline job generation. Minimally assumes that the pipeline
    acts on input files listed in a file manifest file, itself in the so-called
    "BCDC11" format. The schema has 11 fields for each file and includes hashes.
    """
    cached_file_metadata_header = [
        ('Input_file_identifier', 'TEXT'),
        ('Sample_ID', 'TEXT'),
        ('SHA256', 'CHAR(64)'),
        ('File_basename', 'TEXT'),
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
    ):
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

    def generate(self):
        """
        This is the main exposed API call.

        Generates jobs involving input files and write to the jobs subdirectory. Also
        writes scripts that schedule the jobs.
        """
        self.initialize_job_activity_table()
        self.populate_file_metadata_table()
        self.gather_input_info()
        self.clean_directory_area()
        self.generate_all_jobs()
        self.generate_scheduler_scripts()

    def initialize_job_activity_table(self):
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
            if row['Checksum scheme'] != 'SHA256':
                logger.error('Checksum for file with id "%s" is not SHA256. Cannot check file integrity.', file_id)
            if not re.match('^[a-f0-9]{64}$', sha256):
                logger.error('SHA256 checksum %s for file with id "%s" is malformed.', sha256, file_id)
            values_str = ', '.join([
                '"' + file_id + '"',
                '"' + sample_id + '"',
                '"' + sha256 + '"',
                '"' + filename + '"',
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
        self.make_fresh_directory(self.jobs_paths.jobs_path)
        self.make_fresh_directory(self.jobs_paths.logs_path)
        self.make_fresh_directory(self.jobs_paths.output_path)
        for file in os.listdir('./'):
            if re.search('^schedule_.+sh$', file):
                os.remove(file)

    def make_fresh_directory(self, path):
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
        Generate the job script files using local state.
        """
        pass

    def generate_scheduler_scripts(self):
        """
        Generate a bash script or scripts that schedule the jobs.
        """
        pass
