from ....standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class NearestDistanceAnalysisIntegrator:
    """
    Main class of the integration phase.
    """
    def __init__(self,
        computational_design=None,
        **kwargs,
    ):
        """
        :param computational_design: Design object providing metadata specific to the
            density workflow.
        """
        self.computational_design = computational_design

    def calculate(self, filename):
        """
        Performs statistical comparison tests and writes results.
        """
        logger.warning('Stats not implemented.')
        with open(filename, 'wt') as file:
            file.write('')
