"""
This is the module in which should be registered any metadata related to the
design of the nearest-distance-to-compartment workflow.
"""
import re

from spatialprofilingtoolbox.workflow.halo_import.computational_design import HALOImportDesign


class NearestDistanceDesign(HALOImportDesign):
    """Overall workflow design for nearest distance to compartment workflow."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass

    def get_workflow_specific_columns(self, style):
        compartments = self.dataset_design.get_compartments()
        nearest_cell_columns = ['distance to nearest cell ' + compartment
                                for compartment in compartments]
        if style == 'sql':
            nearest_cell_columns = [
                re.sub(r'[\- ]', '_', c) for c in nearest_cell_columns
            ]
        return nearest_cell_columns
