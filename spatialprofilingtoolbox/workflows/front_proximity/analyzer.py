import sqlite3

from ...environment.single_job_analyzer import SingleJobAnalyzer
from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.log_formats import colorized_logger
from .core import FrontProximityCalculator
from .integrator import FrontProximityAnalysisIntegrator
from .computational_design import FrontProximityDesign

logger = colorized_logger(__name__)


class FrontProximityAnalyzer(SingleJobAnalyzer):
    def __init__(self, **kwargs):
        super(FrontProximityAnalyzer, self).__init__(**kwargs)
        self.retrieve_input_filename()
        self.retrieve_sample_identifier()

        self.calculator = FrontProximityCalculator(
            input_filename = self.get_input_filename(),
            sample_identifier = self.get_sample_identifier(),
            dataset_settings = self.dataset_settings,
            dataset_design = self.dataset_design,
            computational_design = self.computational_design,
        )

    def _calculate(self):
        self.calculator.calculate_front_proximity()

    def initialize_intermediate_database(self):
        """
        The front proximity workflow uses a pipeline-specific database to store its
        intermediate outputs. This method initializes this database's tables.
        """
        cell_front_distances_header = self.computational_design.get_cell_front_distances_header()

        connection = sqlite3.connect(self.computational_design.get_database_uri())
        cursor = connection.cursor()
        cmd = ' '.join([
            'CREATE TABLE IF NOT EXISTS',
            'cell_front_distances',
            '(',
            'id INTEGER PRIMARY KEY AUTOINCREMENT,',
            ' , '.join([
                column_name + ' ' + data_type_descriptor for column_name, data_type_descriptor in cell_front_distances_header
            ]),
            ');',
        ])
        cursor.execute(cmd)
        cursor.close()
        connection.commit()
        connection.close()
