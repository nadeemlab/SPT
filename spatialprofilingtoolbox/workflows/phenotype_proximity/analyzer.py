import os
from os.path import dirname

from ...environment.single_job_analyzer import SingleJobAnalyzer
from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.log_formats import colorized_logger
from .core import PhenotypeProximityCalculator
from .integrator import PhenotypeProximityAnalysisIntegrator
from .computational_design import PhenotypeProximityDesign

logger = colorized_logger(__name__)


class PhenotypeProximityAnalyzer(SingleJobAnalyzer):
    def __init__(self,
        dataset_design=None,
        complex_phenotypes_file: str=None,
        **kwargs,
    ):
        """
        Args:

        dataset_design:
            The design object describing the input data set.

        complex_phenotypes_file (str):
            The table of composite phenotypes to be considered.
        """
        super(PhenotypeProximityAnalyzer, self).__init__(**kwargs)
        self.dataset_design = dataset_design
        self.computational_design = PhenotypeProximityDesign(
            dataset_design = self.dataset_design,
            complex_phenotypes_file = complex_phenotypes_file,
        )

        self.retrieve_input_filename()
        self.retrieve_sample_identifier()
        file_id = dataset_design.get_regional_areas_file_identifier()
        regional_areas_file = self.get_input_filename_by_identifier(file_id)

        self.calculator = PhenotypeProximityCalculator(
            input_filename = self.get_input_filename(),
            sample_identifier = self.get_sample_identifier(),
            jobs_paths = self.jobs_paths,
            dataset_settings = self.dataset_settings,
            dataset_design = self.dataset_design,
            computational_design = self.computational_design,
            regional_areas_file = regional_areas_file,
        )

    def _calculate(self):
        self.calculator.calculate_proximity()

    def cell_counts_and_intensity_averages(self):
        """
        (To be deprecated / migrated. Needs to be refactored based on new indexing
        aggregation level.)
        """
        signatures = self.dataset_design.get_all_phenotype_signatures()
        phenotypes = [self.dataset_design.munge_name(signature) for signature in signatures]
        records = []
        intensity_column_names = list(self.dataset_design.get_intensity_column_names().keys())
        for phenotype in phenotypes:

            for i, (filename, single_file_cells) in enumerate(self.cells.items()):
                by_file_fov = single_file_cells.groupby('field of view index')
                for fov_index, df in by_file_fov:
                    index = list(df.index)

                    marked_fov_cells_indices = set(index).intersection(self.phenotype_indices[filename][phenotype])
                    for compartment in list(set(self.dataset_design.get_compartments())) + ['all']:
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
