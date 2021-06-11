import os
from os.path import dirname

from ...dataset_designs.multiplexed_immunofluorescence.design import HALOCellMetadataDesign
from ...environment.single_job_analyzer import SingleJobAnalyzer
from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.log_formats import colorized_logger
from .core import PhenotypeProximityCalculator
from .integrator import PhenotypeProximityAnalysisIntegrator

logger = colorized_logger(__name__)


class PhenotypeProximityAnalyzer(SingleJobAnalyzer):
    def __init__(self,
        outcomes_file: str=None,
        output_path: str=None,
        elementary_phenotypes_file=None,
        complex_phenotypes_file=None,
        **kwargs,
    ):
        super(PhenotypeProximityAnalyzer, self).__init__(**kwargs)
        self.outcomes_file = outcomes_file
        self.output_path = output_path
        self.design = HALOCellMetadataDesign(elementary_phenotypes_file, complex_phenotypes_file)

        self.retrieve_input_filename()
        self.retrieve_sample_identifier()

        self.calculator = PhenotypeProximityCalculator(
            input_filename=self.get_input_filename(),
            sample_identifier=self.get_sample_identifier(),
            outcomes_file=outcomes_file,
            output_path=output_path,
            design=self.design,
        )

    def first_job_started(self):
        logger.info(
            'Beginning multiplexed immunofluorescence cell propinquity analysis.'
        )
        logger.info(
            'Using multiple pixel distance thresholds: %s',
            self.calculator.get_radii_of_interest(),
        )
        logger.info(
            'Input files located at %s.',
            dirname(self.get_input_filename()),
        )
        logger.info(
            'Found outcomes file at %s',
            self.outcomes_file,
        )
        logger.info(
            'Will write results to %s',
            self.output_path,
        )

    def _calculate(self):
        self.calculator.calculate_proximity()

    def start_post_jobs_step(self):
        cell_proximity_integration = PhenotypeProximityAnalysisIntegrator(
            output_path=self.output_path,
            design=self.design,
        )
        cell_proximity_integration.calculate()


    def cell_counts_and_intensity_averages(self):
        """
        Needs to be refactored based on new indexing aggregation level.
        """
        signatures = self.design.get_all_phenotype_signatures()
        phenotypes = [self.design.munge_name(signature) for signature in signatures]
        records = []
        intensity_column_names = list(self.design.get_intensity_column_names().keys())
        for phenotype in phenotypes:

            for i, (filename, single_file_cells) in enumerate(self.cells.items()):
                by_file_fov = single_file_cells.groupby('field of view index')
                for fov_index, df in by_file_fov:
                    index = list(df.index)

                    marked_fov_cells_indices = set(index).intersection(self.phenotype_indices[filename][phenotype])
                    for compartment in list(set(self.design.get_compartments())) + ['all']:
                        if compartment != 'all':
                            marked_fov_cells_indices = marked_fov_cells_indices.intersection(self.compartment_indices[filename][compartment])

                    marked_fov_cells = df[marked_fov_cells_indices]

                    average_intensities = dict(df[intensity_column_names].mean())


            select_phenotype = self.cells.loc[
                (self.cells[phenotype + ' membership'])
            ]

            for compartment in list(set(self.cells['regional compartment'])) + ['all']:
                if compartment != 'all':
                    subselection = select_phenotype[select_phenotype['regional compartment'] == compartment]
                else:
                    subselection = select_phenotype
                c = ['source file name', 'field of view index']
                for [source_filename, fov], df in subselection.groupby(c):
                    average_intensities = dict(df[intensity_column_names].mean())
                    if compartment == 'all':
                        total_in_field = self.get_total_in_field(source_filename, fov)
                        fraction = df.shape[0] / total_in_field
                    else:
                        fraction = None
                    records.append({**
                        {
                            'phenotype' : phenotype,
                            'source file name' : source_filename,
                            'field of view index' : fov,
                            'regional compartment' : compartment,
                            'count' : df.shape[0],
                            'count fraction of all cells in FOV' : fraction,
                        },
                        **average_intensities,
                    })
        cell_counts_and_intensity_averages = pd.DataFrame(records)
        logger.debug('Completed cell counts and intensity average over FOVs.')
