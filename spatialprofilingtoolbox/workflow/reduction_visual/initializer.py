"""The initializer for the phenotype proximity workflow."""
from typing import Optional

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.workflow.component_interfaces.initializer import Initializer


class ReductionVisualInitializer(Initializer): #pylint: disable=too-few-public-methods
    """
    Initial job for the visualization via dimension reduction workflow.
    Creates a dedicated table for the string-encoded plots.
    """

    def __init__(self,
                 database_config_file: Optional[str] = None,
                 **kwargs):
        self.database_config_file = database_config_file

    def initialize(self, **kwargs):
        with DatabaseConnectionMaker(self.database_config_file) as dcm:
            connection = dcm.get_connection()
            cursor = connection.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS visualization_plots (
                identifier integer,
                svg_string bytea,
                target integer,
                study text
                );
            ''', )
            cursor.close()
            connection.commit()


