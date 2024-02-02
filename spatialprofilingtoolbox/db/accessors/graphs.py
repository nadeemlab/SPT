"""Convenience access of cg-gnn metrics."""

from typing import cast

from pandas import (
    DataFrame,
    to_datetime,
)

from spatialprofilingtoolbox.util import STRFTIME_FORMAT
from spatialprofilingtoolbox.db.describe_features import get_feature_description
from spatialprofilingtoolbox.db.database_connection import SimpleReadOnlyProvider


class GraphsAccess(SimpleReadOnlyProvider):
    """Access to graph features from database."""

    def get_important_cells(
        self,
        study: str,
        plugin: str = 'cg-gnn',
        datetime_of_run: str = 'most recent',
        plugin_version: str | None = None,
        cohort_stratifier: str | None = None,
        cell_limit: int = 100,
    ) -> set[int]:
        """Get the cell_limit most important cell IDs for each specimen in this study."""
        if datetime_of_run == 'most recent':
            self.cursor.execute('''
                SELECT
                    fsr.specifier
                FROM feature_specifier fsr
                    JOIN feature_specification fs
                        ON fs.identifier=fsr.feature_specification
                    JOIN study_component sc
                        ON sc.component_study=fs.study
                WHERE fs.derivation_method=%s
                    AND sc.primary_study=%s
                    AND fsr.ordinality='2'
                ORDER BY fsr.specifier DESC
                LIMIT 1
                ;
            ''', (get_feature_description("gnn importance score"), study))
            datetime_of_run = cast(str, self.cursor.fetchone()[0])
        else:
            datetime_of_run = to_datetime(datetime_of_run).strftime(STRFTIME_FORMAT)

        params = [plugin, datetime_of_run]
        fs_identifier_query = '''
            SELECT fs.identifier
            FROM feature_specification fs
                JOIN study_component sc
                    ON sc.component_study=fs.study
                JOIN (
                    SELECT feature_specification
                    FROM feature_specifier
                    WHERE ordinality='1' AND specifier=%s
                ) AS fsr1
                    ON fs.identifier = fsr1.feature_specification
                JOIN (
                    SELECT feature_specification
                    FROM feature_specifier
                    WHERE ordinality='2' AND specifier=%s
                ) AS fsr2
                    ON fs.identifier = fsr2.feature_specification
        '''
        if plugin_version is not None:
            fs_identifier_query += '''
                JOIN (
                    SELECT feature_specification
                    FROM feature_specifier
                    WHERE ordinality='3' AND specifier=%s
                ) AS fsr3
                    ON fs.identifier = fsr3.feature_specification
            '''
            params.append(plugin_version)
        if cohort_stratifier is not None:
            fs_identifier_query += '''
                JOIN (
                    SELECT feature_specification
                    FROM feature_specifier
                    WHERE ordinality='4' AND specifier=%s
                ) AS fsr4
                    ON fs.identifier = fsr4.feature_specification
            '''
            params.append(cohort_stratifier)
        fs_identifier_query += '''
            WHERE sc.primary_study=%s
                AND fs.derivation_method=%s
        '''
        params.extend((study, get_feature_description("gnn importance score")))
        query = f'''
            SELECT
                qfv.subject,
                sdmp.specimen
            FROM quantitative_feature_value qfv
                JOIN histological_structure_identification hsi
                    ON hsi.histological_structure=qfv.subject
                JOIN data_file df
                    ON df.sha256_hash=hsi.data_source
                JOIN specimen_data_measurement_process sdmp
                    ON df.source_generation_process=sdmp.identifier
            WHERE qfv.feature IN (
                {fs_identifier_query}
            )
            ORDER BY sdmp.specimen, qfv.value
            ;
        '''
        self.cursor.execute(query, params)

        rows = self.cursor.fetchall()
        df = DataFrame(rows, columns=['subject', 'sample'])
        truncated = df.groupby('sample').head(cell_limit)
        return set(map(int, truncated['subject']))
