"""Initializer functionality for the phenotype density workflow."""
from spatialprofilingtoolbox.workflow.halo_import.initializer import Initializer


class DensityInitializer(Initializer):
    """
    Density workflow initializer. Currently such setup functionality is needed
    in this workflow.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass
