"""
The parallelizable, job-level analysis stage of the cell phenotype density
analysis workflow.
"""
from os.path import join, abspath, basename
import hashlib
import sqlite3

import pandas as pd

from ..defaults.single_job_analyzer import SingleJobAnalyzer
from ...environment.log_formats import colorized_logger
from .core import DensityCalculator
from .computational_design import DensityDesign

logger = colorized_logger(__name__)


class DensityAnalyzer(SingleJobAnalyzer):
    """
    The main class of the job.
    """
    def __init__(
        self,
        **kwargs,
    ):
        super(DensityAnalyzer, self).__init__(**kwargs)
        self.calculator = DensityCalculator(
            input_filename = self.get_input_filename(),
            sample_identifier = self.get_sample_identifier(),
            outcome = self.get_outcome(),
            dataset_design = self.dataset_design,
            computational_design = self.computational_design,
        )

    @staticmethod
    def solicit_cli_arguments(parser):
        pass

    def _calculate(self):
        self.calculator.calculate_density()

    def initialize_metrics_database(self):
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

        # Check if fov_lookup is still used
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
