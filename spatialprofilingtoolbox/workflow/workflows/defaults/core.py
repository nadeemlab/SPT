import os
from os.path import getsize
import re

import pandas as pd

from ...common.file_io import raw_line_count
from ...common.dichotomization import Dichotomizer
from ...common.logging.performance_timer import PerformanceTimer
from ....standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CoreJob:
    def __init__(
        self,
        dataset_design=None,
        computational_design=None,
        input_file_identifier: str=None,
        input_filename: str=None,
        sample_identifier: str=None,
        outcome: str=None,
        **kwargs,
    ):
        """
        :param dataset_design: Design object providing metadata about the *kind* of
            input data being provided.

        :param computational_design: Design object providing metadata specific to the
            density workflow.
        """
        self.dataset_design = dataset_design
        self.computational_design = computational_design
        self.input_file_identifier = input_file_identifier
        self.input_filename = input_filename
        self.sample_identifier = sample_identifier
        self.outcome = outcome
        self.timer = PerformanceTimer()

    def initialize_metrics_database(self):
        """
        Initialize the local sqlite database for intermediate metrics. The URI is
        provided by computational_design.get_database_uri() .
        """
        pass

    def _calculate(self):
        """
        Abstract method, the implementation of which is the core/primary computation to
        be performed by this job.
        """
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
        self.wrap_up_timer()

    def wrap_up_timer(self):
        """
        Concludes low-level performance metric collection for this job.
        """
        df = self.timer.report(by='fraction')
        df.to_csv(self.computational_design.get_performance_report_filename(), index=False)

    def log_file_info(self):
        number_cells = raw_line_count(self.input_filename) - 1
        logger.info('%s cells to be parsed from source file "%s".', number_cells, self.input_filename)
        logger.info('Cells source file has size %s bytes.', getsize(self.input_filename))

    def get_table(self, filename):
        table_from_file = pd.read_csv(filename)
        self.preprocess(table_from_file)
        return table_from_file

    def preprocess(self, table):
        if self.computational_design.dichotomize:
            for phenotype in self.dataset_design.get_elementary_phenotype_names():
                intensity = self.dataset_design.get_intensity_column_name(phenotype)
                if not intensity in table.columns:
                    self.dataset_design.add_combined_intensity_column(table, phenotype)
                Dichotomizer.dichotomize(
                    phenotype,
                    table,
                    dataset_design=self.dataset_design,
                )
                feature = self.dataset_design.get_feature_name(phenotype)
                if not feature in table.columns:
                    feature = re.sub(' ', '_', feature)
                    if not feature in table.columns:
                        message = 'Feature %s not in columns.', feature
                        logger.error(message)
                        raise ValueError(message)
                number_positives = sum(table[feature])
                logger.info(
                    'Dichotomization column "%s" written. %s positives.',
                    feature,
                    number_positives,
                )
        else:
            logger.info('Not performing thresholding.')

        fov = self.dataset_design.get_FOV_column()
        if fov in table.columns:
            str_values = [str(element) for element in table[fov]]
            table[fov] = str_values
        else:
            logger.debug('Creating dummy "%s" until its use is fully deprecated.', fov)
            table[fov] = ['FOV1' for i, row in table.iterrows()]
