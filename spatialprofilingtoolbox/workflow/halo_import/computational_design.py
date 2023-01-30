"""The design parameters of the main data import workflow."""
from spatialprofilingtoolbox.workflow.defaults.computational_design import ComputationalDesign


class HALOImportDesign(ComputationalDesign):
    """Overall workflow design parameters for import workflow."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass

    @staticmethod
    def uses_database():
        return True
