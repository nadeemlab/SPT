"""The wrap-up functionality for the front proximity workflow."""
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class FrontProximityAnalysisIntegrator:
    """Integration phase of front proximity workflow."""
    def __init__(self, computational_design=None):
        """
        Args:
            computational_design:
                Design object providing metadata specific to the front proximity pipeline.
        """
        self.computational_design = computational_design
        self.cell_proximity_tests = None

    def get_cell_proximity_tests(self):
        return self.cell_proximity_tests

    def calculate(self, filename):
        """
        Performs statistical comparison tests and writes results.
        """
        logger.info('<Stats calculation not implemented>')
        with open(filename, 'wt', encoding='utf-8') as file:
            file.write('')
