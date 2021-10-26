"""
Generation of the job scripts and job scheduling scripts for the proximity
workflow.
"""

from ...environment.job_generator import JobGenerator
from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class PhenotypeProximityJobGenerator(JobGenerator):
    def __init__(self,
        **kwargs,
    ):
        super(PhenotypeProximityJobGenerator, self).__init__(**kwargs)

    def gather_input_info(self):
        pass

    def job_specification_by_file(self):
        return True
