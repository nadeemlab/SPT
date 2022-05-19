
from ..defaults.integrator import Integrator
from ...environment.logging.log_formats import colorized_logger

logger = colorized_logger(__name__)


class NearestDistanceAnalysisIntegrator(Integrator):
    """
    Main class of the integration phase.
    """
    def __init__(self, **kwargs):
        super(NearestDistanceAnalysisIntegrator, self).__init__(**kwargs)

    def calculate(self):
        """
        Performs statistical comparison tests and writes results.
        """
        logger.info('<Stats calculation not implemented>')
        with open(self.stats_tests_file, 'wt') as file:
            file.write('')
