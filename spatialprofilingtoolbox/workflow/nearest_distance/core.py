"""
The core/parallelizable functionality of the nearest distance to compartment
workflow.
"""
from scipy.spatial import KDTree

from spatialprofilingtoolbox.workflow.nearest_distance.computational_design import \
    NearestDistanceDesign
from spatialprofilingtoolbox.workflow.halo_import.core import FileBasedCoreJob
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class NearestDistanceCoreJob(FileBasedCoreJob):
    """
    Core/parellelizable functionality for the nearest distance to a compartment
    workflow.
    """
    computational_design: NearestDistanceDesign

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass

    def _calculate(self):
        self.write_cell_data()

    def write_cell_data(self):
        """
        Writes cell data to the database.

        Note that in the density analysis workflow, much calculation takes place in
        the "integration" phase.
        """
        self.timer.record_timepoint('Starting calculation of density')
        cells, fov_lookup = self.create_cell_table()
        logger.info('Aggregated %s cells into table.', cells.shape[0])
        self.write_cell_table(cells)
        self.write_fov_lookup_table(fov_lookup)
        logger.info('Finished writing cells and fov lookup helper.')

    def add_nearest_cell_data(self, table, compartment):
        compartments = self.dataset_design.get_compartments()
        cell_indices = list(table.index)
        xmin, xmax, ymin, ymax = self.dataset_design.get_box_limit_column_names()
        table['x value'] = 0.5 * (table[xmax] + table[xmin])
        table['y value'] = 0.5 * (table[ymax] + table[ymin])
        signature = self.dataset_design.get_compartmental_signature(
            table, compartment)
        if sum(signature) == 0:
            for i, cell_index in enumerate(cell_indices):
                table.loc[cell_index, 'distance to nearest cell ' +
                          compartment] = -1
        else:
            compartment_cells = table[signature]
            compartment_points = [
                (row['x value'], row['y value'])
                for i, row in compartment_cells.iterrows()
            ]
            all_points = [
                (row['x value'], row['y value'])
                for i, row in table.iterrows()
            ]
            tree = KDTree(compartment_points)
            distances, _ = tree.query(all_points)
            for i, cell_index in enumerate(cell_indices):
                compartment_i = table.loc[cell_index, 'compartment']
                if compartment_i == compartment:
                    distance = 0
                elif compartment_i not in compartments:
                    distance = -1
                else:
                    distance = distances[i]
                table.loc[cell_index, 'distance to nearest cell ' +
                          compartment] = distance

    def get_and_add_extra_columns(self, table):
        self.timer.record_timepoint('Adding distance-to-nearest data')
        for compartment in self.dataset_design.get_compartments():
            self.add_nearest_cell_data(table, compartment)
        nearest_cell_columns = [
            'distance to nearest cell ' + compartment
            for compartment in self.dataset_design.get_compartments()]
        self.timer.record_timepoint('Finished adding distance-to-nearest data')
        return nearest_cell_columns
