"""
This is the module in which should be registered any metadata related to the
design of the cell phenotype density analysis workflow.
"""
import re

from spatialprofilingtoolbox.workflow.defaults.computational_design import ComputationalDesign


class DensityDesign(ComputationalDesign):
    """
    The design object.
    """

    def __init__(self, use_intensities: bool = False, **kwargs):
        """
        :param use_intensities: Whether to use continuous channel intensity values.
        :type use_intensities: bool
        """
        super().__init__(**kwargs)
        self.use_intensities = use_intensities

    @staticmethod
    def solicit_cli_arguments(parser):
        pass

    def get_workflow_specific_columns(self, style):
        return self.get_intensity_columns(style=style, values_only=True)

    def get_intensity_columns(self, style='readable', values_only=False):
        if self.use_intensities:
            intensity_names = self.dataset_design.get_elementary_phenotype_names()
            intensity_columns = [(name, name + ' intensity')
                                 for name in intensity_names]
            intensity_columns = sorted(
                intensity_columns, key=lambda pair: pair[0])
            if style == 'sql':
                intensity_columns = [
                    (name, re.sub(' ', '_', c)) for name, c in intensity_columns
                ]
            if values_only:
                intensity_columns = [pair[1] for pair in intensity_columns]
        else:
            intensity_columns = []
        return intensity_columns
