"""
A single job of the proximity workflow.
"""

import pandas as pd

from ...environment.single_job_analyzer import SingleJobAnalyzer
from ...environment.file_io import get_input_filename_by_identifier
from ...environment.log_formats import colorized_logger
from .core import PhenotypeProximityCalculator
from .computational_design import PhenotypeProximityDesign

logger = colorized_logger(__name__)


class PhenotypeProximityAnalyzer(SingleJobAnalyzer):
    """
    The main class of the single job.
    """
    def __init__(self, **kwargs):
        super(PhenotypeProximityAnalyzer, self).__init__(**kwargs)

        self.retrieve_input_filename()
        self.retrieve_sample_identifier()
        file_id = self.dataset_design.get_regional_areas_file_identifier()
        regional_areas_file = get_input_filename_by_identifier(
            dataset_settings = self.dataset_settings,
            file_metadata = pd.read_csv(self.dataset_settings.file_manifest_file, sep='\t'),
            input_file_identifier = file_id,
        )

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
