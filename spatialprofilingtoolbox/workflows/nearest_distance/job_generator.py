"""
Generation of the job scripts and job scheduling scripts for the cell
phenotype density analysis workflow.
"""

from ..defaults.job_generator import JobGenerator
from ...environment.logging.log_formats import colorized_logger

logger = colorized_logger(__name__)


class NearestDistanceJobGenerator(JobGenerator):
    def __init__(self,
        **kwargs,
    ):
        super(NearestDistanceJobGenerator, self).__init__(**kwargs)
