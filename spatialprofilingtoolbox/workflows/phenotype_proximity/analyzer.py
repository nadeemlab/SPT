"""
A single job of the proximity workflow.
"""

from ...environment.single_job_analyzer import SingleJobAnalyzer
from ...environment.log_formats import colorized_logger
from .core import PhenotypeProximityCalculator
from .computational_design import PhenotypeProximityDesign

logger = colorized_logger(__name__)


class PhenotypeProximityAnalyzer(SingleJobAnalyzer):
    """
    The main class of the single job.
    """
    def __init__(self,
        dataset_design: PhenotypeProximityDesign=None,
        complex_phenotypes_file: str=None,
        computational_design: PhenotypeProximityDesign=None,
        **kwargs,
    ):
        """
        :param dataset_design: The design object describing the input data set.

        :param complex_phenotypes_file: The table of composite phenotypes to be
            considered.
        :type complex_phenotypes_file: str

        :param balanced: Whether to use balanced or unbalanced treatment of phenotype
            pairs.
        :type balanced: bool
        """
        super(PhenotypeProximityAnalyzer, self).__init__(**kwargs)
        self.dataset_design = dataset_design
        self.computational_design = computational_design

        self.retrieve_input_filename()
        self.retrieve_sample_identifier()
        file_id = dataset_design.get_regional_areas_file_identifier()
        regional_areas_file = self.get_input_filename_by_identifier(file_id)

        self.calculator = PhenotypeProximityCalculator(
            input_filename = self.get_input_filename(),
            sample_identifier = self.get_sample_identifier(),
            jobs_paths = self.jobs_paths,
            dataset_settings = self.dataset_settings,
            dataset_design = self.dataset_design,
            computational_design = self.computational_design,
            regional_areas_file = regional_areas_file,
        )

    def _calculate(self):
        self.calculator.calculate_proximity()
