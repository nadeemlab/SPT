"""
Generation of the job scripts and job scheduling scripts for the cell
phenotype density analysis workflow.
"""

from ..defaults.job_generator import JobGenerator
from ...environment.source_file_parsers.skimmer import DataSkimmer
from ...environment.logging.log_formats import colorized_logger

logger = colorized_logger(__name__)


class HALOImportInitializer(JobGenerator):
    def __init__(self,
        **kwargs,
    ):
        super(HALOImportInitializer, self).__init__(**kwargs)

        with DataSkimmer(
            dataset_design = self.dataset_design,
            input_path = input_files_path,
            file_manifest_file = file_manifest_file,
        ) as skimmer:
            skimmer.parse()
