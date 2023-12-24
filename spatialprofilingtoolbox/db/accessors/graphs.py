"""Convenience access of cg-gnn metrics."""
from typing import cast
from pandas import DataFrame

from spatialprofilingtoolbox.db.describe_features import get_feature_description
from spatialprofilingtoolbox.db.database_connection import SimpleReadOnlyProvider
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import CGGNNImportanceRank


class GraphsAccess(SimpleReadOnlyProvider):
    """Access to graph features from database."""

    def get_metrics(self, study: str, cell_limit: int | None = None) -> list[CGGNNImportanceRank]:
        """Get graph metrics for this study.

        Returns
        -------
        list[CGGNNImportanceRank]
            List of (histological structure ID, importance rank) tuples.
        """
        parameters: list[str | int] = [get_feature_description("gnn importance score"), study]
        if cell_limit is not None:
            parameters.append(cell_limit)
        self.cursor.execute(f'''
            SELECT
                qfv.subject,
                qfv.value
            FROM quantitative_feature_value qfv
                JOIN feature_specification fs
                    ON fs.identifier=qfv.feature
                JOIN study_component sc
                    ON sc.component_study=fs.study
            WHERE fs.derivation_method=%s
                AND sc.primary_study=%s
                {'AND qfv.value < %s' if (cell_limit is not None) else ''}
            ;
        ''', parameters)
        rows = self.cursor.fetchall()
        return [CGGNNImportanceRank(
            histological_structure_id=int(row[0]),
            rank=int(row[1])
        ) for row in rows]

    def get_important_cells(self, study: str, cell_limit: int) -> set[int]:
        """Get the cell_limit most important cell IDs for each specimen in this study."""
        self.cursor.execute('''
            SELECT
                qfv.subject, sdmp.specimen
            FROM quantitative_feature_value qfv
                JOIN feature_specification fs
                    ON fs.identifier=qfv.feature
                JOIN histological_structure_identification hsi
                    ON hsi.histological_structure=qfv.subject
                JOIN data_file df
                    ON df.sha256_hash=hsi.data_source
                JOIN specimen_data_measurement_process sdmp
                    ON df.source_generation_process=sdmp.identifier
                JOIN study_component sc
                    ON sc.component_study=fs.study
            WHERE fs.derivation_method=%s
                AND sc.primary_study=%s
            ORDER BY sdmp.specimen, qfv.value
            ;
        ''', (get_feature_description("gnn importance score"), study))
        rows = self.cursor.fetchall()
        df = DataFrame(rows, columns=['subject', 'sample'])
        truncated = df.groupby('sample').head(cell_limit)
        return set(map(int, truncated['subject']))
