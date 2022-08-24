
from ..defaults.initializer import Initializer


class NearestDistanceInitializer(Initializer):
    def __init__(self,
        **kwargs,
    ):
        super(NearestDistanceInitializer, self).__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass
