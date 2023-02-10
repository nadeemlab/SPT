"""
Generate a list of parallelizable jobs for the proximity metric calculation
pipeline.
"""

import pandas as pd

from spatialprofilingtoolbox.workflow.component_interfaces.job_generator import JobGenerator
from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class ProximityJobGenerator(JobGenerator):
    """
    Generate a list of parallelizable jobs for the proximity metric calculation
    pipeline.
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
        return ProximityJobGenerator.retrieve_sample_identifiers_from_db(
            self.study_name, self.database_config_file)

    @staticmethod
    def retrieve_sample_identifiers_from_db(study_name, database_config_file):
        with DatabaseConnectionMaker(database_config_file=database_config_file) as maker:
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
            cursor.execute(query, (study_name,))
            rows = cursor.fetchall()
            cursor.close()
        return [row[0] for row in rows]

    def write_job_specification_table(self, job_specification_table_filename):
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
