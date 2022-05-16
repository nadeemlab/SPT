

class Initializer:
    def __init__(
        self,
        dataset_design = None,
        computational_design = None,
        **kwargs,
    ):
        self.dataset_design = dataset_design
        self.computational_design = computational_design
        pass

    def solicit_cli_parameters(self, parser):
        pass

    def initialize(self, **kwargs):
        pass
