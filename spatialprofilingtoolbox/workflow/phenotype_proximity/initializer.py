"""The initializer for the phenotype proximity workflow."""
from spatialprofilingtoolbox.workflow.defaults.initializer import Initializer


class PhenotypeProximityInitializer(Initializer):
    """
    Initial job for the phenotype proximity metrics computation workflow.
    Currently no such initialization functionality is needed.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass
