
from ..defaults.initializer import Initializer


class PhenotypeProximityInitializer(Initializer):
    def __init__(self,
        **kwargs,
    ):
        super(PhenotypeProximityInitializer, self).__init__(**kwargs)

    def solicit_cli_parameters(self, parser):
        pass
