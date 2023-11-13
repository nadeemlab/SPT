"""Generate a list of parallelizable jobs for the visualization pipeline."""

import pandas as pd

from spatialprofilingtoolbox.workflow.component_interfaces.job_generator import JobGenerator
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.workflow.common.job_generator import \
    retrieve_sample_identifiers_from_db
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class ReductionVisualJobGenerator(JobGenerator):
    """Job generator for visualization workflow."""
    def __init__(self, study_name, database_config_file):
        self.database_config_file = database_config_file
        self.study_name = self.validate_study_name(study_name)

    def validate_study_name(self, study_name):
        with DBCursor(database_config_file=self.database_config_file) as cursor:
            query = 'SELECT DISTINCT study FROM study_lookup WHERE study=%s;'
            cursor.execute(query, (study_name,))
            rows = cursor.fetchall()
        if len(rows) == 1:
            return rows[0][0]
        raise ValueError(f'Could not locate study named: {study_name}')

    def retrieve_sample_identifiers(self):
        return ReductionVisualJobGenerator.retrieve_sample_identifiers_from_db(
            self.study_name, self.database_config_file)

    @staticmethod
    def retrieve_sample_identifiers_from_db(study_name, database_config_file):
        return retrieve_sample_identifiers_from_db(study_name, database_config_file)

    def write_job_specification_table(self, job_specification_table_filename):
        rows = [{'job_index': 0}]
        df = pd.DataFrame(rows)
        df.to_csv(job_specification_table_filename, index=False, header=True)
