
from ..defaults.initializer import Initializer


class DensityInitializer(Initializer):
    def __init__(self, **kwargs):
        super(DensityInitializer, self).__init__(**kwargs)

    def solicit_cli_arguments(self, parser):
        pass
