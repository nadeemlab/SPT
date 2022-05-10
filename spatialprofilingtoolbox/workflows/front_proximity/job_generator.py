"""
Generation of the job scripts and job scheduling scripts for the front
proximity workflow.
"""

from ..defaults.job_generator import JobGenerator
from ...environment.logging.log_formats import colorized_logger

logger = colorized_logger(__name__)


class FrontProximityJobGenerator(JobGenerator):
    def __init__(self,
        **kwargs,
    ):
        super(FrontProximityJobGenerator, self).__init__(**kwargs)
