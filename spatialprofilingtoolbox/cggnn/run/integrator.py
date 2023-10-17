"""The integration phase of the CG GNN workflow. Uploads results to database."""

from pandas import read_csv

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.importance_score_transcriber import transcribe_importance
from spatialprofilingtoolbox.workflow.component_interfaces.integrator import Integrator
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CGGNNIntegrator(Integrator):
    """Integrate CG GNN results into the database."""

    def __init__(
        self,
        database_config_file: str | None = None,
        cohort_stratifier: str = '',
        **kwargs
    ) -> None:
        self.cohort_stratifier = cohort_stratifier
        self.database_config_file = database_config_file

    def calculate(self, cggnn_importance_results_files: list[str] | None, **kwargs) -> None:
        """Upload some CG GNN pipeline results to database."""
        if cggnn_importance_results_files is not None:
            connection = DatabaseConnectionMaker(self.database_config_file).get_connection()
            for filename in cggnn_importance_results_files:
                logger.info('Uploading importance file %s to database.', filename)
                transcribe_importance(
                    read_csv(filename, index_col=0),
                    connection,
                    cohort_stratifier=self.cohort_stratifier,
                )
            connection.close()
