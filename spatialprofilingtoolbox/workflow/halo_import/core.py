import sqlite3

from ..defaults.core import CoreJob
from ....standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class HALOImportCoreJob(CoreJob):
    def __init__(self, **kwargs):
        super(HALOImportCoreJob, self).__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass

    def _calculate(self):
        self.timer.record_timepoint('Will parse cells.')
        self.parse_cells()
        self.timer.record_timepoint('Done parsing cells.')

    def initialize_metrics_database(self):
        connection = sqlite3.connect(self.computational_design.get_database_uri())
        cursor = connection.cursor()
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
