"""The initializer for the phenotype proximity workflow."""
from spatialprofilingtoolbox.workflow.tabular_import.initializer import Initializer
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument


class PhenotypeProximityInitializer(Initializer):
    """
    Initial job for the phenotype proximity metrics computation workflow.
    Currently no such initialization functionality is needed.
    """

    @staticmethod
    def solicit_cli_arguments(parser):
        add_argument(parser, 'study name')

    def initialize(self, **kwargs):
        pass
