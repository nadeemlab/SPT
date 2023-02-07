"""
Interface class for the functionality of creating a manifest of the
parallelizable jobs to be done as part of a given workflow.
"""

import pandas as pd

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class ProximityJobGenerator:
    """
    An interface for pipeline job generation. Minimally assumes that the pipeline
    acts on input files listed in a file manifest file, itself in a format
    controlled by a relatively precise schema (distributed with the source code of
    this package).
    """

    def __init__(self, study_name, database_config_file):
        self.database_config_file = database_config_file
        self.study_name = self.validate_study_name(study_name)

    def validate_study_name(self, study_name):
        with DatabaseConnectionMaker(database_config_file=self.database_config_file) as maker:
            connection = maker.get_connection()
            cursor = connection.cursor()
            query = 'SELECT DISTINCT primary_study FROM study_component ;'
            cursor.execute(query, (study_name,))
            rows = cursor.fetchall()
            cursor.close()
        if study_name in [row[0] for row in rows]:
            return study_name
        raise ValueError(f'Could not locate study named: {study_name}')

    def retrieve_sample_identifiers(self):
        with DatabaseConnectionMaker(database_config_file=self.database_config_file) as maker:
            connection = maker.get_connection()
            cursor = connection.cursor()
            query = '''
            SELECT scp.specimen
            FROM specimen_collection_process scp
            JOIN study_component sc ON sc.component_study=scp.study
            WHERE sc.primary_study=%s
            AND EXISTS (SELECT sdmp.identifier FROM specimen_data_measurement_process sdmp WHERE sdmp.specimen=scp.specimen)
            ORDER BY scp.specimen
            ;            '''
            cursor.execute(query, (self.study_name,))
            rows = cursor.fetchall()
            cursor.close()
        return [row[0] for row in rows]

    def write_job_specification_table(self, job_specification_table_filename):
        """
        Prepares the job specification table for the orchestrator.
        """
        samples = self.retrieve_sample_identifiers()
        rows = [
            {
                'job_index': i,
                'sample_identifier': sample,
            }
            for i, sample in enumerate(samples)
        ]
        df = pd.DataFrame(rows)
        columns = df.columns
        df = df[sorted(columns)]
        df.to_csv(job_specification_table_filename, index=False, header=True)
