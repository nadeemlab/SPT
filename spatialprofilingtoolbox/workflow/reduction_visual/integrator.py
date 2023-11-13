"""The integration phase of the reduction visualization workflow."""

from spatialprofilingtoolbox.workflow.component_interfaces.integrator import Integrator
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class ReductionVisualAnalysisIntegrator(Integrator):  # pylint: disable=too-few-public-methods
    """The main class of the integration phase."""
    
    def __init__(self,
        study_name: str='',
        database_config_file: str | None = None,
        **kwargs # pylint: disable=unused-argument
    ):
        self.study_name = study_name
        self.database_config_file = database_config_file

    def calculate(self, **kwargs):
        logger.info("Nothin' to see here.")
