
import pandas as pd

from .dichotomization import Dichotomizer
from .log_formats import colorized_logger

logger = colorized_logger(__name__)


class Calculator:
    def __init__(
        self,
        dataset_design=None,
        computational_design=None,
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

    def get_table(self, filename):
        table_from_file = pd.read_csv(filename)
        self.preprocess(table_from_file)
        return table_from_file

    @staticmethod
    def pull_in_outcome_data(outcomes_file):
        """
        :param outcomes_file: Name of file with outcomes data.
        :type outcomes_file: str

        :return outcomes: Dictionary whose keys are sample identifiers, and values are
            outcome labels.
        :rtype outcomes: dict
        """
        outcomes_table = pd.read_csv(outcomes_file, sep='\t')
        columns = outcomes_table.columns
        outcomes_dict = {
            row[columns[0]]: str(row[columns[1]]) for i, row in outcomes_table.iterrows()
        }
        return outcomes_dict

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
