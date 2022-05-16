
from ..defaults.initializer import Initializer


class FrontProximityInitializer(Initializer):
    def __init__(self,
        **kwargs,
    ):
        super(FrontProximityInitializer, self).__init__(**kwargs)

    def solicit_cli_arguments(self, parser):
        pass
