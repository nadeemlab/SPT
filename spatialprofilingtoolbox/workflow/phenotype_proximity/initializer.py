"""The initializer for the phenotype proximity workflow."""
from spatialprofilingtoolbox.workflow.component_interfaces.initializer import Initializer


class PhenotypeProximityInitializer(Initializer): #pylint: disable=too-few-public-methods
    """
    Initial job for the phenotype proximity metrics computation workflow.
    Currently no such initialization functionality is done.
    """

    def initialize(self, **kwargs):
        pass
