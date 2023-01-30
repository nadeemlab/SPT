"""The parameters of the overall design of the front proximity workflow."""
from spatialprofilingtoolbox.workflow.defaults.computational_design import ComputationalDesign


class FrontProximityDesign(ComputationalDesign):
    """Overal workflow design parameters for the front proximity workflow."""

    def __init__(self,
                 **kwargs,
                 ):
        """
        :param dataset_design: The design object describing the input data set.
        """
        super().__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass

    def get_cell_front_distances_header(self):
        """
        Returns:
            list:
                A list of 2-tuples, column name followed by SQL-style datatype name,
                describing the schema for the cell-to-front distances intermediate data
                table.
        """
        return [
            ('sample_identifier', 'TEXT'),
            ('fov_index', 'INTEGER'),
            ('outcome_assignment', 'TEXT'),
            ('phenotype', 'TEXT'),
            ('compartment', 'TEXT'),
            ('other_compartment', 'TEXT'),
            ('distance_to_front_in_pixels', 'NUMERIC'),
        ]
