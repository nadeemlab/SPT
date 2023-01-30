"""
Interface for a class meant to describe the design of the overall workflow,
for a given workflow.
"""

import pandas as pd

from spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.halo_cell_metadata_design\
    import HALOCellMetadataDesign
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class ComputationalDesign:
    """
    Subclass this object to collect together any metadata that is specific to a
    particular pipeline/workflow's computation stage.
    """

    def __init__(self,
                 dataset_design: HALOCellMetadataDesign,
                 metrics_database_filename: str = 'metrics_default.db',
                 dichotomize: bool = False,
                 composite_phenotypes_file: str = '',
                 **kwargs,  # pylint: disable=unused-argument
                 ):
        """
        :param dataset_design: The design object describing the input data set.

        :param metrics_database_filename: Name for sqlite database.
        :type metrics_database_filename: str

        :param dichotomize: Default False. Whether to do auto-thresholding to
            dichotomize the continuous input variables.
        :type dichotomize: bool
        """
        self.dataset_design = dataset_design
        self.metrics_database_filename = metrics_database_filename
        self.complex_phenotypes = pd.read_csv(
            composite_phenotypes_file,
            keep_default_na=False,
        )
        self.dichotomize = dichotomize

    @staticmethod
    def solicit_cli_arguments(parser):
        parser.add_argument(
            '--metrics-database-filename',
            dest='metrics_database_filename',
            type=str,
            required=True,
        )
        parser.add_argument(
            '--composite-phenotypes-file',
            dest='composite_phenotypes_file',
            type=str,
            required=True,
        )
        parser.add_argument(
            '--dichotomize',
            dest='dichotomize',
            action='store_true',
        )

    def get_database_uri(self):
        return self.metrics_database_filename

    def get_performance_report_filename(self):
        return self.metrics_database_filename.rstrip('.db') + '.csv'

    @staticmethod
    def uses_database():
        return False

    def get_all_phenotype_signatures(self):
        """
        :return: The "signatures" for all the composite phenotypes described by the
            ``complex_phenotypes_file`` table. Each signature is a dictionary with keys
            the elementary phenotype names and values either "+" or "-".
        :rtype: list
        """
        elementary_signatures = [
            {name: '+'} for name in self.dataset_design.get_elementary_phenotype_names()
        ]
        complex_signatures = []
        for _, row in self.complex_phenotypes.iterrows():
            positive_markers = sorted(
                [m for m in row['Positive markers'].split(';') if m != ''])
            negative_markers = sorted(
                [m for m in row['Negative markers'].split(';') if m != ''])
            signature = {}
            for marker in positive_markers:
                signature[marker] = '+'
            for marker in negative_markers:
                signature[marker] = '-'
            complex_signatures.append(signature)
        return elementary_signatures + complex_signatures
