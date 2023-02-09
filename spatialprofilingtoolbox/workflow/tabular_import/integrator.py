"""The wrap-up task of the main data import workflow."""

from spatialprofilingtoolbox.workflow.tabular_import.computational_design import TabularImportDesign
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class TabularImportIntegrator:
    """
    Wrap-up phase of the data import workflow. Currently no wrap-up is needed.
    """
    def __init__(self, **kwargs): # pylint: disable=unused-argument
        self.computational_design = TabularImportDesign(**kwargs)

    def get_computational_design(self):
        return self.computational_design

    def calculate(self, filename):
        logger.info('Doing integration.')
        with open(filename, 'wt', encoding='utf-8') as file:
            file.write('')
