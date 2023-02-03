"""Core/parallelizable functionality for the phenotype density workflow."""
from spatialprofilingtoolbox.workflow.density.computational_design import DensityDesign
from spatialprofilingtoolbox.workflow.defaults.core import CoreJob
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
from spatialprofilingtoolbox.workflow.density.data_logging import DensityDataLogger

logger = colorized_logger(__name__)


class DensityCoreJob(CoreJob):
    """Main parallelizable functionality for phenotype density workflow."""
    computational_design: DensityDesign

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass

    def _calculate(self):
        self.calculate_density()

    def calculate_density(self):
        """
        Writes cell data to the database.

        Note that in the density analysis workflow, much calculation takes place in
        the "integration" phase.
        """
        self.timer.record_timepoint('Starting calculation of density')
        cells, fov_lookup = self.create_cell_table()
        logger.info('Aggregated %s cells into table.', cells.shape[0])
        DensityDataLogger.log_number_by_type(self.computational_design, cells)
        self.write_cell_table(cells)
        self.write_fov_lookup_table(fov_lookup)
        logger.info('Finished writing cells and fov lookup helper.')

    def get_and_add_extra_columns(self, table):
        if self.computational_design.use_intensities:
            self.overlay_intensities(table)
            self.timer.record_timepoint('Overlaid intensities')
            intensity_columns = self.computational_design.get_intensity_columns(
                values_only=True)
        else:
            intensity_columns = []
        return intensity_columns

    def overlay_intensities(self, table):
        intensity_columns = self.computational_design.get_intensity_columns()
        for phenotype_name, column_name in intensity_columns:
            intensity = self.dataset_design.get_combined_intensity(
                table, phenotype_name)
            table[column_name] = intensity
