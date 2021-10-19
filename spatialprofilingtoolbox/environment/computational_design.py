
import pandas as pd

from .log_formats import colorized_logger

logger = colorized_logger(__name__)


class ComputationalDesign:
    """
    Subclass this object to collect together any metadata that is specific to a
    particular pipeline/workflow's computation stage.
    """
    def __init__(self,
        complex_phenotypes_file: str=None,
        dichotomize: bool=False,
        **kwargs,
    ):
        """
        :param complex_phenotypes_file: The table of composite phenotypes to be
            considered.
        :type complex_phenotypes_file: str

        :param dichotomize: Default False. Whether to do auto-thresholding to
            dichotomize the continuous input variables.
        :type dichotomize: bool
        """
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
