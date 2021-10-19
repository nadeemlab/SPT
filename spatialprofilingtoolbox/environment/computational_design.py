
import pandas as pd

from .file_io import get_input_filename_by_identifier
from .log_formats import colorized_logger

logger = colorized_logger(__name__)


class ComputationalDesign:
    """
    Subclass this object to collect together any metadata that is specific to a
    particular pipeline/workflow's computation stage.
    """
    def __init__(self,
        dataset_design=None,
        dichotomize: bool=False,
        **kwargs,
    ):
        """
        :param dataset_design: The design object describing the input data set.

        :param dichotomize: Default False. Whether to do auto-thresholding to
            dichotomize the continuous input variables.
        :type dichotomize: bool
        """
        self.dataset_design = dataset_design
        self.dataset_settings = self.dataset_design.dataset_settings
        complex_phenotypes_file = get_input_filename_by_identifier(
            dataset_settings = self.dataset_settings,
            file_metadata = pd.read_csv(self.dataset_settings.file_manifest_file, sep='\t'),
            input_file_identifier = 'Complex phenotypes file',
        )
        self.complex_phenotypes = pd.read_csv(
            complex_phenotypes_file,
            keep_default_na=False,
        )
        self.dichotomize = dichotomize

    def get_database_uri(self):
        """
        Each computational workflow may request persistent storage of intermediate data.
        The implementation class should provide the URI of the database in which to
        store this data.

        Currently, only local sqlite databases are supported. Future version may
        support remote SQL database connections.

        :return: The Uniform Resource Identifier (URI) identifying the database.
        :rtype: str
        """
        pass
