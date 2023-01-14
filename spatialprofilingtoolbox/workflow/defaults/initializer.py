from abc import ABC, abstractmethod


class Initializer(ABC):

    def __init__(
        self,
        dataset_design=None,
        computational_design=None,
        **kwargs,
    ):
        self.dataset_design = dataset_design
        self.computational_design = computational_design

    @staticmethod
    @abstractmethod
    def solicit_cli_arguments(parser):
        pass

    def initialize(self, **kwargs):
        pass
