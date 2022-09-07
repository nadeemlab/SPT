
from ....standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class HALOImportIntegrator:
    def __init__(
        self,
        computational_design=None,
        **kwargs,
    ):
        self.computational_design = computational_design

    def calculate(self, filename):
        logger.info('Doing integration.')
        open(filename, 'wt').write('')
