"""Convenience access of cg-gnn metrics."""

from spatialprofilingtoolbox import get_feature_description
from spatialprofilingtoolbox.db.accessors.study import StudyAccess
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
        components = StudyAccess(self.cursor).get_study_components(study)
        self.cursor.execute(f'''
            SELECT
                qfv.subject,
                qfv.value
            FROM quantitative_feature_value qfv
                JOIN feature_specification fs
                    ON fs.identifier=qfv.feature
            WHERE fs.derivation_method='{get_feature_description("gnn importance score")}'
                AND fs.study='{components.analysis}'
                {'AND qfv.value < ' + str(cell_limit) if (cell_limit is not None) else ''}
            ;
        ''')
        rows = self.cursor.fetchall()
        return [CGGNNImportanceRank(
            histological_structure_id=int(row[0]),
            rank=int(row[1])
        ) for row in rows]

    def get_important_cells(self, study: str, cell_limit: int) -> set[int]:
        """Get the cell_limit most important cell IDs for each specimen in this study."""
        components = StudyAccess(self.cursor).get_study_components(study)
        self.cursor.execute(f'''
            SELECT
                qfv.subject
            FROM quantitative_feature_value qfv
                JOIN feature_specification fs
                    ON fs.identifier=qfv.feature
            WHERE fs.derivation_method='{get_feature_description("gnn importance score")}'
                AND fs.study='{components.analysis}'
                AND qfv.value < {cell_limit}  -- Importance is 0-indexed
            ;
        ''')
        rows = self.cursor.fetchall()
        return set(int(row[0]) for row in rows)
