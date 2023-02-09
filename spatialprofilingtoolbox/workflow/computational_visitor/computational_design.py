"""Parameters for the overall design of the "computational visitor" workflow pattern."""

from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class ComputationalVisitorDesign:
    """
    The computational visitor pattern is about visiting a database, retrieving
    some data, processing it, then returning back results right back to the
    database.
    """

    def __init__(self, **kwargs):  # pylint: disable=unused-argument
        pass

    @staticmethod
    def solicit_cli_arguments(parser):
        add_argument(parser, 'database config')
        add_argument(parser, 'performance report')

    def get_performance_report_filename(self):
        return 'performance_report.csv'

    def get_all_phenotype_signatures(self):
        pass

    def get_phenotype_signatures_by_name(self):
        pass

    def get_phenotype_names(self):
        pass
