
from ..defaults.initializer import Initializer


class DensityInitializer(Initializer):
    def __init__(self, **kwargs):
        super(DensityInitializer, self).__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass
