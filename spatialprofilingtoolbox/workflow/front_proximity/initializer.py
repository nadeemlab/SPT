"""The initializer for the front proximity workflow."""
from spatialprofilingtoolbox.workflow.defaults.initializer import Initializer


class FrontProximityInitializer(Initializer):
    def __init__(self,
        **kwargs,
    ):
        super(FrontProximityInitializer, self).__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass