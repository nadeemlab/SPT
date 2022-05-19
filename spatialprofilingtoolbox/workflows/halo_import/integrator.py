
from ..defaults.integrator import Integrator
from ...environment.logging.log_formats import colorized_logger

logger = colorized_logger(__name__)


class HALOImportIntegrator(Integrator):
    def __init__(self, **kwargs):
        super(HALOImportIntegrator, self).__init__(**kwargs)

    def calculate(self):
        logger.info('<Stats calculation not implemented>')
        open(self.stats_tests_file, 'wt').write('')
