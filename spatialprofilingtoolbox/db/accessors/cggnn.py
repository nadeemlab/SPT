"""Convenience access of cg-gnn metrics."""

from spatialprofilingtoolbox import get_feature_description
from spatialprofilingtoolbox.db.accessors.study import StudyAccess
from spatialprofilingtoolbox.db.database_connection import SimpleReadOnlyProvider
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import CGGNNImportanceRank


class CGGNNAccess(SimpleReadOnlyProvider):
    """Access to cg-gnn features from database."""

    def get_metrics(self, study: str) -> list[CGGNNImportanceRank]:
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
            ;
        ''')
        rows = self.cursor.fetchall()
        return [CGGNNImportanceRank(
            histological_structure_id=int(row[0]),
            rank=int(row[1])
        ) for row in rows]
