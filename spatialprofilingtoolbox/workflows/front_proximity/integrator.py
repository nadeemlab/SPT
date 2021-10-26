
from ...environment.file_io import get_outcomes_files
from ...environment.settings_wrappers import DatasetSettings
from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class FrontProximityAnalysisIntegrator:
    def __init__(self,
        dataset_settings: DatasetSettings=None,
        computational_design=None,
        **kwargs,
    ):
        """
        Args:
            dataset_settings (DatasetSettings):
                Convenience bundle of paths to input dataset files.
            computational_design:
                Design object providing metadata specific to the front proximity pipeline.
        """
        self.outcomes_file = get_outcomes_files(dataset_settings)[0]
        self.computational_design = computational_design
        self.cell_proximity_tests = None

    def calculate(self):
        """
        Performs statistical comparison tests and writes results.
        """
        logger.info('<Stats calculation not implemented>')
