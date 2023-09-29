"""Convenience access of cg-gnn metrics."""

from spatialprofilingtoolbox import get_feature_description
from spatialprofilingtoolbox.db.database_connection import SimpleReadOnlyProvider
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import CGGNNImportanceRank


class CGGNNAccess(SimpleReadOnlyProvider):
    """Access to cg-gnn features from database."""

    def get_metrics(self, study: str, cell_limit: int | None = None) -> list[CGGNNImportanceRank]:
        """Get cg-gnn metrics for this study.

        Returns
        -------
        list[CGGNNImportanceRank]
            List of (histological structure ID, importance rank) tuples.
        """
        parameters = [get_feature_description("gnn importance score"), study]
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
                qfv.subject
            FROM quantitative_feature_value qfv
                JOIN feature_specification fs
                    ON fs.identifier=qfv.feature
                JOIN study_component sc
                    ON sc.component_study=fs.study
            WHERE fs.derivation_method=%s
                AND sc.primary_study=%s
                AND qfv.value < %s  -- Importance is 0-indexed
            ;
        ''', (get_feature_description("gnn importance score"), study, cell_limit))
        rows = self.cursor.fetchall()
        return set(int(row[0]) for row in rows)
