"""Retrieve outcome data for all studies."""
from typing import cast

from pandas import DataFrame
from psycopg2.extensions import cursor as Psycopg2Cursor

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

Stratification = dict[str, dict[str, DataFrame]]


class StratificationPuller:
    """Retrieve sample cohort data for all studies."""

    cursor: Psycopg2Cursor
    stratification: dict | None

    def __init__(self, cursor: Psycopg2Cursor):
        self.cursor = cursor
        self.stratification = None

    def pull(self, measured_only: bool = False) -> None:
        """Pull specimens and their strata (sample cohort) from the database.

        Parameters
        ----------
        measured_only : bool = False
            Whether to select only for specimens that were measured. If False, all collected
            specimens, even those that didn't have measurements taken, are collected.
        """
        self.stratification = self._retrieve_stratification(measured_only=measured_only)

    def get_stratification(self) -> Stratification:
        return cast(dict, self.stratification)

    def _retrieve_stratification(self, measured_only: bool = False) -> Stratification:
        study_names = self._get_study_names()
        stratification: Stratification = {}
        for study_name in study_names:
            self.cursor.execute(f'''
            SELECT
                scp.study,
                sample,
                stratum_identifier,
                local_temporal_position_indicator,
                subject_diagnosed_condition,
                subject_diagnosed_result
            FROM sample_strata
                JOIN specimen_collection_process scp
                    ON sample=scp.specimen
                JOIN study_component sc
                    ON sc.component_study=scp.study {"""
                JOIN specimen_data_measurement_process sdmp
                    ON sdmp.specimen=scp.specimen""" if measured_only else ""}
            WHERE sc.primary_study=%s
            ;
            ''', (study_name,))
            rows = self.cursor.fetchall()
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

    def _get_study_names(self) -> tuple[str, ...]:
        self.cursor.execute('SELECT study_specifier FROM study ;')
        rows = self.cursor.fetchall()
        study_names = [row[0] for row in rows]
        return tuple(sorted(study_names))
