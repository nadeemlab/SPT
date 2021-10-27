"""
The parallelizable, job-level analysis stage of the cell phenotype density
analysis workflow.
"""
from os.path import join, abspath, basename
import hashlib
import sqlite3

import pandas as pd

from ...environment.single_job_analyzer import SingleJobAnalyzer
from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.log_formats import colorized_logger
from .core import DensityCalculator
from .computational_design import DensityDesign

logger = colorized_logger(__name__)


class DensityAnalyzer(SingleJobAnalyzer):
    """
    The main class of the job.
    """
    def __init__(self,
        skip_integrity_check=False,
        **kwargs,
    ):
        super(DensityAnalyzer, self).__init__(**kwargs)
        sample_identifiers_by_file = self.retrieve_cell_input_file_info(skip_integrity_check)
        self.calculator = DensityCalculator(
            sample_identifiers_by_file = sample_identifiers_by_file,
            dataset_settings = self.dataset_settings,
            dataset_design = self.dataset_design,
            computational_design = self.computational_design,
        )
        logger.info('Job started.')
        logger.info('Note: The "density" workflow operates as a single job.')

    def _calculate(self):
        self.calculator.calculate_density()

    def retrieve_cell_input_file_info(self, skip_integrity_check):
        """
        :param skip_integrity_check: Whether to calculate checksums and verify that they
            match what appears in the manifest. This option is provided to speed up
            repeated runs.
        :type skip_integrity_check: bool

        :return: Information about the input files with cell data. A dictionary whose
            keys are absolute file paths, and values are sample identifiers associated
            with the files.
        :rtype: dict
        """
        if skip_integrity_check:
            logger.info('Skipping file integrity checks.')

        file_metadata = pd.read_csv(self.dataset_settings.file_manifest_file, sep='\t')

        sample_identifiers_by_file = {}
        for i, row in file_metadata.iterrows():
            if not self.dataset_design.validate_cell_manifest_descriptor(row['Data type']):
                continue
            input_file = row['File name']
            sample_identifier = row['Sample ID']
            expected_sha256 = row['Checksum']
            input_file = abspath(join(self.dataset_settings.input_path, input_file))

            if not skip_integrity_check:
                buffer_size = 65536
                sha = hashlib.sha256()
                with open(input_file, 'rb') as file:
                    while True:
                        data = file.read(buffer_size)
                        if not data:
                            break
                        sha.update(data)
                sha256 = sha.hexdigest()
                if sha256 != expected_sha256:
                    logger.error(
                        'File "%s" has wrong SHA256 hash (%s ; expected %s).',
                        row['File name'],
                        sha256,
                        expected_sha256,
                    )
            sample_identifiers_by_file[basename(input_file)] = sample_identifier
        return sample_identifiers_by_file

    def initialize_intermediate_database(self):
        """
        The density workflow uses a pipeline-specific database to store its
        intermediate outputs. This method initializes this database's tables.
        """
        cells_header = self.computational_design.get_cells_header(style='sql')
        connection = sqlite3.connect(self.computational_design.get_database_uri())
        cursor = connection.cursor()
        cmd = ' '.join([
            'CREATE TABLE IF NOT EXISTS',
            'cells',
            '(',
            'id INTEGER PRIMARY KEY AUTOINCREMENT,',
            ', '.join([' '.join(entry) for entry in cells_header]),
            ');',
        ])
        cursor.execute(cmd)
        cursor.close()
        connection.commit()
        connection.close()

        fov_lookup_header = self.computational_design.get_fov_lookup_header()
        connection = sqlite3.connect(self.computational_design.get_database_uri())
        cursor = connection.cursor()
        cmd = ' '.join([
            'CREATE TABLE IF NOT EXISTS',
            'fov_lookup',
            '(',
            'id INTEGER PRIMARY KEY AUTOINCREMENT,',
            ', '.join([' '.join(entry) for entry in fov_lookup_header]),
            ');',
        ])
        cursor.execute(cmd)
        cursor.close()
        connection.commit()
        connection.close()
