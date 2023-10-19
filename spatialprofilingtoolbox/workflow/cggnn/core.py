"""The core calculator for CG GNN modeling on a given study."""

from cggnn import run
from pandas import DataFrame

from spatialprofilingtoolbox.cggnn import extract_cggnn_data
from spatialprofilingtoolbox.workflow.component_interfaces.core import CoreJob
from spatialprofilingtoolbox.workflow.common.logging.performance_timer import \
    PerformanceTimerReporter
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CGGNNCoreJob(CoreJob):
    """Core/parallelizable functionality for the CG GNN workflow."""

    def __init__(
        self,
        study_name: str = '',
        database_config_file: str = '',
        performance_report_file: str = '',
        results_file: str = '',
        strata: list[int] | None = None,
        **kwargs
    ) -> None:
        self.study_name = study_name
        self.database_config_file = database_config_file
        self.strata = strata
        self.results_file = results_file
        self.reporter = PerformanceTimerReporter(performance_report_file, logger)

    def _calculate(self):
        df_cell, df_label, label_to_result = extract_cggnn_data(
            self.database_config_file,
            self.study_name,
            self.strata,
        )
        model, importances = run(df_cell, df_label, label_to_result)
        DataFrame.from_dict(
            importances,
            orient='index',
            columns=['importance_score'],
        ).to_csv(self.results_file)
        self.reporter.wrap_up_timer()
