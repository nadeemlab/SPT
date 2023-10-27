"""Retrieve outcome data for all studies."""
from typing import cast

from pandas import DataFrame
from psycopg2.extensions import cursor as Psycopg2Cursor

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import retrieve_study_names
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

Stratification = dict[str, dict[str, DataFrame]]

class StratificationPuller:
    """Retrieve sample cohort data for all studies."""

    database_config_file: str | None
    stratification: dict | None

    def __init__(self, database_config_file: str | None):
        self.database_config_file = database_config_file
        self.stratification = None

    def pull(self) -> None:
        self.stratification = self._retrieve_stratification()

    def get_stratification(self) -> Stratification:
        return cast(dict, self.stratification)

    def _retrieve_stratification(self) -> Stratification:
        stratification: Stratification = {}
        study_names = retrieve_study_names(self.database_config_file)
        for study_name in study_names:
            with DBCursor(database_config_file=self.database_config_file, study=study_name) as cursor:
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
                rows = cursor.fetchall()
                if len(rows) == 0:
                    continue
            columns = [
                'specimen collection study',
                'specimen',
                'stratum identifier',
                'local temporal position indicator',
                'subject diagnosed condition',
                'subject diagnosed result',
            ]
            df = DataFrame(rows, columns=columns)
            substudy_name = list(df['specimen collection study'])[0]
            stratification[substudy_name] = {}
            assignments_columns = ['specimen', 'stratum identifier']
            stratification[substudy_name]['assignments'] = df[assignments_columns]
            metadata_columns = [
                'stratum identifier',
                'local temporal position indicator',
                'subject diagnosed condition',
                'subject diagnosed result',
            ]
            stratification[substudy_name]['strata'] = df[metadata_columns].drop_duplicates()
        return stratification
