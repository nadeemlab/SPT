"""Convenience access of cg-gnn metrics."""

from spatialprofilingtoolbox import get_feature_description
from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor
from spatialprofilingtoolbox.db.accessors.study import StudyAccess
from spatialprofilingtoolbox.db.database_connection import SimpleReadOnlyProvider
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import (
    CGGNNImportanceRank,
    UnivariateMetricsComputationResult,
)


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

    def get_importance_composition(
        self,
        study: str,
        positive_markers: set[str],
        negative_markers: set[str],
        cell_limit: int = 100,
    ) -> UnivariateMetricsComputationResult:
        """For each specimen, return the fraction of important cells expressing the given phenotype.

        Parameters
        ----------
        study : str
            Study name.
        positive_markers : set[str]
        negative_markers : set[str]
            Phenotype signature.
        cell_limit : int = 100
            Find the fraction of cells in the top `cell_limit` most important cells that express
            the given phenotype.
        """
        if cell_limit < 1:
            raise ValueError(f'`cell_limit` must be at least 1, not {cell_limit}.')

        components = StudyAccess(self.cursor).get_study_components(study)
        self.cursor.execute(f'''
            SELECT
                qfv.subject AS histological_structure
            FROM quantitative_feature_value qfv
                JOIN feature_specification fs
                    ON fs.identifier=qfv.feature
            WHERE fs.derivation_method='{get_feature_description("gnn importance score")}'
                AND fs.study='{components.analysis}'
                AND qfv.value < {cell_limit}  -- Importance is 0-indexed
            ;
        ''')
        rows = self.cursor.fetchall()
        important_ids = {int(row[0]) for row in rows}

        # This could be faster if we only looked up the channels for important cells and not all
        extractor = FeatureMatrixExtractor(cursor=self.cursor)
        bundles = extractor.extract(study=study, retain_structure_id=True)
        positive_column_names = [f'C {marker}' for marker in positive_markers]
        negative_column_names = [f'C {marker}' for marker in negative_markers]
        specimen_to_proportion: dict[str, float] = {}
        for specimen, bundle in bundles.items():
            df_important = bundle.dataframe.loc[bundle.dataframe.index.isin(important_ids),]
            specimen_to_proportion[specimen] = (
                df_important[positive_column_names].all(axis=1) &
                ~df_important[negative_column_names].any(axis=1)
            ).sum() / cell_limit

        rows = self.cursor.fetchall()
        return UnivariateMetricsComputationResult(
            values=specimen_to_proportion,
            is_pending=False,
        )
