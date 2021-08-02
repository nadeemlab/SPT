
from ...environment.single_job_analyzer import SingleJobAnalyzer
from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.log_formats import colorized_logger
from .core import FrontProximityCalculator
from .integrator import FrontProximityAnalysisIntegrator
from .computational_design import FrontProximityDesign

logger = colorized_logger(__name__)


class FrontProximityAnalyzer(SingleJobAnalyzer):
    def __init__(self,
        dataset_design=None,
        complex_phenotypes_file: str=None,
        **kwargs,
    ):
        """
        Args:

        dataset_design:
            The design object describing the input data set.

        complex_phenotypes_file (str):
            The table of composite phenotypes to be considered.
        """
        super(FrontProximityAnalyzer, self).__init__(**kwargs)
        self.dataset_design = dataset_design
        self.computational_design = FrontProximityDesign(
            dataset_design = self.dataset_design,
            complex_phenotypes_file = complex_phenotypes_file,
        )

        self.retrieve_input_filename()
        self.retrieve_sample_identifier()

        self.calculator = FrontProximityCalculator(
            input_filename = self.get_input_filename(),
            sample_identifier = self.get_sample_identifier(),
            jobs_paths = self.jobs_paths,
            dataset_settings = self.dataset_settings,
            dataset_design = self.dataset_design,
            computational_design = self.computational_design,
        )

    def _calculate(self):
        self.calculator.calculate_front_proximity()
