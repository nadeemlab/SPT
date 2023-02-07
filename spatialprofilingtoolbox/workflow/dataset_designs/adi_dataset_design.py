"""
Design parameters for a dataset (often HALO generated) to be imported by the
main import workflow.
"""

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class ADIDatasetDesign:
    """
    This class provides some interface to the ADI single cell studies schema.
    """

    def __init__(self, **kwargs):  # pylint: disable=unused-argument
        pass

    @staticmethod
    def solicit_cli_arguments(parser):
        pass

    def munge_name(self, signature):
        """
        Args:
            signature (dict):
                The keys are typically phenotype names and the values are "+" or "-". If
                a key is not a phenotype name, it is presumed to be the exact name of
                one of the columns in the HALO-exported CSV. In this case the value
                should be an exact string of one of the cell values of this CSV.

        Returns:
            str:
                A de-facto name for the class delineated by this signature, obtained by
                concatenating key/value pairs in a standardized order.
        """
        feature_list = [key + signature[key] for key in signature]
        name = ''.join(feature_list)
        return name
