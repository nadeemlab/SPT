"""Retrieve outcome data for all studies."""
import pandas as pd

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class StratificationPuller(DatabaseConnectionMaker):
    """Retrieve sample cohort data for all studies."""
    def __init__(self, database_config_file):
        super().__init__(database_config_file=database_config_file)
        self.stratification = None

    def pull(self):
        self.stratification = self.retrieve_stratification()

    def get_stratification(self):
        return self.stratification

    def retrieve_stratification(self):
        study_names = self.get_study_names()
        stratification = {}
        with self.get_connection().cursor() as cursor:
            for study_name in study_names:
                cursor.execute('''
                SELECT
                    scp.study,
                    sample,
                    stratum_identifier,
                    local_temporal_position_indicator,
                    subject_diagnosed_condition,
                    subject_diagnosed_result
                FROM
                    sample_strata
                JOIN
                    specimen_collection_process scp ON sample=scp.specimen
                JOIN
                    study_component sc ON sc.component_study=scp.study
                WHERE
                    sc.primary_study=%s
                ;
                ''', (study_name,))
                df = pd.DataFrame(cursor.fetchall(), columns=['specimen collection study',
                                  'specimen',
                                  'stratum identifier',
                                  'local temporal position indicator',
                                  'subject diagnosed condition', 'subject diagnosed result'])
                substudy_name = list(df['specimen collection study'])[0]
                stratification[substudy_name] = {}
                assignments_columns = ['specimen', 'stratum identifier']
                stratification[substudy_name]['assignments'] = df[assignments_columns]
                metadata_columns = ['stratum identifier', 'local temporal position indicator',
                                    'subject diagnosed condition', 'subject diagnosed result']
                stratification[substudy_name]['strata'] = df[metadata_columns].drop_duplicates()
        return stratification

    def get_study_names(self):
        with self.get_connection().cursor() as cursor:
            cursor.execute('SELECT study_specifier FROM study ;')
            rows = cursor.fetchall()
        study_names = [row[0] for row in rows]
        return sorted(study_names)
