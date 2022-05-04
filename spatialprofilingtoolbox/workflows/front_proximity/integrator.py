
from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class FrontProximityAnalysisIntegrator:
    def __init__(self,
        computational_design=None,
        **kwargs,
    ):
        """
        Args:
            computational_design:
                Design object providing metadata specific to the front proximity pipeline.
        """
        self.computational_design = computational_design
        self.cell_proximity_tests = None

    def calculate(self):
        """
        Performs statistical comparison tests and writes results.
        """
        logger.info('<Stats calculation not implemented>')
