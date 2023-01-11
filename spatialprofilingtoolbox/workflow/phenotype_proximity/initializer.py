
from ..defaults.initializer import Initializer


class PhenotypeProximityInitializer(Initializer):
    def __init__(self,
        **kwargs,
    ):
        super(PhenotypeProximityInitializer, self).__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass
