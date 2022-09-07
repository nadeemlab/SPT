
import pandas as pd

from ....standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class ComputationalDesign:
    """
    Subclass this object to collect together any metadata that is specific to a
    particular pipeline/workflow's computation stage.
    """
    def __init__(self,
        dataset_design=None,
        metrics_database_filename: str='metrics_default.db',
        dichotomize: bool=False,
        composite_phenotypes_file:str = None,
        **kwargs,
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
