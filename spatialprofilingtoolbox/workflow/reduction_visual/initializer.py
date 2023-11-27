"""The initializer for the reduction visualization workflow."""

from typing import Optional

from spatialprofilingtoolbox.workflow.component_interfaces.initializer import Initializer
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class ReductionVisualInitializer(Initializer):  # pylint: disable=too-few-public-methods
    """Initial job for the visualization via dimension reduction workflow.

    Creates a dedicated table for the string-encoded plots.
    """

    def __init__(self, database_config_file: Optional[str] = None, **kwargs):
        self.database_config_file = database_config_file

    def initialize(self, **kwargs):
        logger.info('No initialization to do for UMAP workflow.')
