from itertools import takewhile
from itertools import repeat
import os
from os.path import getsize

import pandas as pd

from .log_formats import colorized_logger

logger = colorized_logger(__name__)


class SingleJobAnalyzer:
    """
    An interface for a single job to be executed as part of a batch in a pipeline
    run. It handles some "boilerplate".
    """
    def __init__(self,
        input_file_identifier: str=None,
        input_filename: str=None,
        sample_identifier: str=None,
        dataset_design=None,
        computational_design=None,
        **kwargs,
    ):
        self.input_file_identifier = input_file_identifier
        self.input_filename = input_filename
        self.sample_identifier = sample_identifier
        self.dataset_design = dataset_design
        self.computational_design = computational_design

    def _calculate(self):
        """
        Abstract method, the implementation of which is the core/primary computation to
        be performed by this job.
        """
        pass

    def initialize_metrics_database(self):
        pass

    def calculate(self):
        """
        The main calculation of this job, to be called by pipeline orchestration.
        """
        self.initialize_metrics_database()
        logger.info('Started core calculator job.')
        self.log_file_info()
        self._calculate()
        logger.info('Completed core calculator job.')

    def log_file_info(self):
        filename = self.get_input_filename()
        number_cells = self.raw_count(filename) - 1
        logger.info('%s cells to be parsed from source file "%s".', number_cells, filename)
        logger.info('Cells source file has size %s bytes.', getsize(filename))

    def raw_count(self, filename):
        f = open(filename, 'rb')
        bufgen = takewhile(lambda x: x, (f.raw.read(1024*1024) for _ in repeat(None)))
        return sum( buf.count(b'\n') for buf in bufgen )

    def get_input_filename(self):
        return self.input_filename

    def get_sample_identifier(self):
        return self.sample_identifier
