
from ...environment.settings_wrappers import JobsPaths, DatasetSettings
from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class FrontProximityAnalysisIntegrator:
    def __init__(
        self,
        jobs_paths: JobsPaths=None,
        dataset_settings: DatasetSettings=None,
        computational_design=None,
        **kwargs,
    ):
        """
        Args:
            jobs_paths (JobsPaths):
                Convenience bundle of filesystem paths pertinent to a particular run at the job level.
            dataset_settings (DatasetSettings):
                Convenience bundle of paths to input dataset files.
            computational_design:
                Design object providing metadata specific to the front proximity pipeline.
        """
        self.output_path = jobs_paths.output_path
        self.outcomes_file = dataset_settings.outcomes_file
        self.computational_design = computational_design
        self.cell_proximity_tests = None

    def calculate(self):
        """
        Performs statistical comparison tests and writes results.
        """
        logger.info('<Stats calculation not implemented>')
