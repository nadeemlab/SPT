
from ..defaults.computational_design import ComputationalDesign


class HALOImportDesign(ComputationalDesign):
    def __init__(self, **kwargs):
        super(HALOImportDesign, self).__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass

    @staticmethod
    def uses_database():
        return True
