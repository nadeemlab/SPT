
from ..defaults.integrator import Integrator
from ...environment.logging.log_formats import colorized_logger

logger = colorized_logger(__name__)


class FrontProximityAnalysisIntegrator(Integrator):
    def __init__(self, **kwargs):
        super(FrontProximityAnalysisIntegrator, self).__init__(**kwargs)
        self.cell_proximity_tests = None

    def calculate(self):
        logger.info('<Stats calculation not implemented>')
        with open(self.stats_tests_file, 'wt') as file:
            file.write('')
        
