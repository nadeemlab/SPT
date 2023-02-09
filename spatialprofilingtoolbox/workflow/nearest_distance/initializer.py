"""The initializer of the nearest distance to compartment workflow."""
from spatialprofilingtoolbox.workflow.halo_import.initializer import Initializer


class NearestDistanceInitializer(Initializer):
    """Initializer job for the nearest distance to compartment workflow."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass
