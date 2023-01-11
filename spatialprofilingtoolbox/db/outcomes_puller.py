
import pandas as pd

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class OutcomesPuller(DatabaseConnectionMaker):
    def __init__(self, database_config_file):
        super(OutcomesPuller, self).__init__(
            database_config_file=database_config_file)
        self.outcomes = None

    def pull(self):
        self.outcomes = self.retrieve_outcomes()

    def get_outcomes(self):
        return self.outcomes

    def retrieve_outcomes(self):
        study_names = self.get_study_names()
        outcomes = {study_name: {} for study_name in study_names}
        with self.get_connection().cursor() as cursor:
            for study_index, study_name in enumerate(study_names):
                cursor.execute('''
                SELECT scp.specimen, d.condition, d.result
                FROM diagnosis d
                JOIN specimen_collection_process scp ON scp.source=d.subject
                WHERE study=%s
                ;
                ''', (study_name,))

                df = pd.DataFrame(cursor.fetchall(), columns=[
                                  'specimen', 'outcome', 'label'])
                dfs = {
                    outcome: df2.sort_values(by='specimen').rename(
                        columns={'label': outcome}).drop(['outcome'], axis=1)
                    for outcome, df2 in df.groupby('outcome')
                }
                merged = pd.concat([dfs[outcome]
                                   for outcome in sorted(list(dfs.keys()))])
                outcomes[study_name]['dataframe'] = merged
                outcomes[study_name]['filename'] = 'outcomes.%s.tsv' % study_index
        return outcomes

    def get_study_names(self):
        with self.get_connection().cursor() as cursor:
            cursor.execute('SELECT name FROM specimen_collection_study ;')
            rows = cursor.fetchall()
        study_names = [row[0] for row in rows]
        return sorted(study_names)
