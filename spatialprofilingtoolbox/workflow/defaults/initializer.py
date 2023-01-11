

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

    @staticmethod
    def solicit_cli_arguments(parser):
        pass

    def initialize(self, **kwargs):
        pass
