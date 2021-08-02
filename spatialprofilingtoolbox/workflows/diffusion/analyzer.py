import os
from os.path import join, dirname
import re

from ...environment.single_job_analyzer import SingleJobAnalyzer
from ...environment.job_generator import JobActivity
from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.log_formats import colorized_logger
from .integrator import DiffusionAnalysisIntegrator
from .computational_design import DiffusionDesign
from .core import DiffusionCalculator, DistanceTypes

logger = colorized_logger(__name__)


class DiffusionAnalyzer(SingleJobAnalyzer):
    def __init__(self,
        dataset_design=None,
        complex_phenotypes_file: str=None,
        fov_index: int=None,
        regional_compartment: str=None,
        **kwargs,
    ):
        """
        Args:
            dataset_design:
                The design object describing the input data set.
            complex_phenotypes_file (str):
                The table of composite phenotypes to be considered.
            fov_index (int):
                The integer index of the field of view to be considered by this job.
            regional_compartment (str):
                The regional compartment (in the sense of
                ``diffusion.job_generator.get_regional_compartments()``) in which
                reside the cells to be considered by this job.
        """
        super(DiffusionAnalyzer, self).__init__(**kwargs)
        self.regional_compartment = regional_compartment

        self.dataset_design = dataset_design
        self.computational_design = DiffusionDesign(
            dataset_design = dataset_design,
            complex_phenotypes_file = complex_phenotypes_file,
        )

        self.retrieve_input_filename()
        self.calculator = DiffusionCalculator(
            input_filename = self.get_input_filename(),
            fov_index = fov_index,
            regional_compartment = regional_compartment,
            dataset_design = self.dataset_design,
            jobs_paths = self.jobs_paths,
        )

    def _calculate(self):
        try:
            markers = self.dataset_design.get_elementary_phenotype_names()
            for distance_type in DistanceTypes:
                if distance_type != DistanceTypes.EUCLIDEAN:
                    continue
                for marker in markers:
                    if not marker in ['DAPI', 'CK']:
                        self.dispatch_diffusion_calculation(distance_type, marker)
                logger.debug('Completed analysis %s (%s)',
                    self.get_job_index(),
                    distance_type.name,
                )
                self.save_job_metadata(distance_type)
        except Exception as e:
            logger.error('Job failed: %s', e)
            self.register_activity(JobActivity.FAILED)
            raise e

    def dispatch_diffusion_calculation(self, distance_type, marker):
        """
        Delegates the main job calculation to ``diffusion.core``.

        Args:
            distance_type (DistanceTypes):
                Type of distance considered as underlying point-set metric for the
                purposes of the diffusion calculation.
            marker (str):
                The elementary phenotype name whose positive cells are to be considered.
        """
        self.calculator.calculate_diffusion(distance_type, marker)

        values = self.calculator.get_values('diffusion kernel')
        if values is not None:
            self.save_transition_probability_values(
                values=values,
                distance_type_str=distance_type.name,
                marker=marker,
            )

        for t in self.calculator.get_temporal_offsets():
            values = self.calculator.get_values(t)
            self.save_transition_probability_values(
                values=values,
                distance_type_str=distance_type.name,
                temporal_offset=t,
                marker=marker,
            )

    def save_transition_probability_values(
        self,
        values=None,
        distance_type_str: str=None,
        temporal_offset=None,
        marker:str=None,
    ):
        """
        Exports results from ``diffusion.core`` calculation.

        Args:
            values:
                List of numeric transition probability values to save.
            distance_type_str (str):
                The distance type (point-set metric) for the context in which the values
                were computed.
            temporal_offset (float):
                The time duration for running the Markov chain process.
            marker (str):
                The elementary phenotype name for the context in which the values were
                computed.
        """
        if temporal_offset is None:
            temporal_offset = 'NULL'

        uri = join(self.jobs_paths.output_path, self.computational_design.get_database_uri())
        with WaitingDatabaseContextManager(uri) as m:
            for value in values:
                m.execute(' '.join([
                    'INSERT INTO',
                    'transition_probabilities',
                    '(' + ', '.join(self.computational_design.get_probabilities_table_header()) + ')',
                    'VALUES',
                    '(' + str(value) +', "' + distance_type_str + '", ' + str(self.get_job_index()) + ', ' + str(temporal_offset) + ', ' + '"' + marker + '"' + ' ' + ');'
                ]))
            m.commit()

    def save_job_metadata(self, distance_type):
        """
        After a given sub-job (for a particular distance type) is complete, this method
        saves this completion state and some other information to the job metadata
        table.

        Args:
            distance_type (DistanceTypes):
                The point-set metric type used for the given sub-job.
        """
        keys = self.computational_design.get_job_metadata_header()
        keys = [re.sub(' ', '_', key) for key in keys]
        values = [
            self.input_file_identifier,
            self.get_sample_identifier(),
            JobActivity.COMPLETE.name,
            self.regional_compartment,
            self.job_index,
            distance_type.name,
        ]

        cmd = ' '.join([
            'INSERT INTO',
            'job_metadata',
            '( ' + ', '.join(keys) + ' )',
            'VALUES',
            '( ' + ', '.join(['"' + str(value) + '"' for value in values]) + ' )',
            ';'
        ])

        uri = join(self.jobs_paths.output_path, self.computational_design.get_database_uri())
        with WaitingDatabaseContextManager(uri) as m:
            m.execute_commit(cmd)
