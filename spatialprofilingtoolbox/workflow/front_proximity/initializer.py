"""The initializer for the front proximity workflow."""
from spatialprofilingtoolbox.workflow.defaults.initializer import Initializer


class FrontProximityInitializer(Initializer):
    """
    Initializer job for the front proximity workflow. Currently no such setup
    is needed in this workflow.
    """
    def __init__(self, **kwargs,):
        super().__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass
