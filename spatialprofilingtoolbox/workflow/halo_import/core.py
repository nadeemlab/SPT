"""The core/parallelizable functionality of the main data import workflow."""

from spatialprofilingtoolbox.workflow.defaults.core import CoreJob
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class HALOImportCoreJob(CoreJob):
    """
    The parallelizable (per file) part of the import workflow. Currently this
    kind of a dummy implementation, beacuse a global view of the dataset is
    needed in order to parse it.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass

    def _calculate(self):
        self.timer.record_timepoint('Will parse cells.')
        self.parse_cells()
        self.timer.record_timepoint('Done parsing cells.')

    def initialize_metrics_database(self):
        connection, cursor = super().connect_to_intermediate_database()
        cmd = ' '.join([
            'CREATE TABLE IF NOT EXISTS',
            'dummy',
            '(',
            'id INTEGER PRIMARY KEY AUTOINCREMENT',
            ');',
        ])
        cursor.execute(cmd)
        cursor.close()
        connection.commit()
        connection.close()

    def parse_cells(self):
        logger.info('Parsing cells from %s', self.input_filename)
