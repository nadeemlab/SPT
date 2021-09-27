
from .log_formats import colorized_logger

logger = colorized_logger(__name__)


class ComputationalDesign:
    """
    Subclass this object to collect together any metadata that is specific to a
    particular pipeline/workflow's computation stage.
    """
    def __init__(self, dichotomize: bool=False, **kwargs):
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
