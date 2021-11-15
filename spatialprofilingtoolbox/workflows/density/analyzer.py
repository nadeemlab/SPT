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
        self.retrieve_input_filename()
        self.retrieve_sample_identifier()
        self.calculator = DensityCalculator(
            input_filename = self.get_input_filename(),
            sample_identifier = self.get_sample_identifier(),
            dataset_settings = self.dataset_settings,
            dataset_design = self.dataset_design,
            computational_design = self.computational_design,
        )
        logger.info('Density job started.')

    def _calculate(self):
        self.calculator.calculate_density()

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
