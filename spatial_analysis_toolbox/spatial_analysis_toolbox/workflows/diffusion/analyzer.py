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
        )

    def first_job_started(self):
        logger.info(
            'Beginning diffusion cell geometry analysis.'
        )
        logger.info(
            'Input files located at %s.',
            dirname(self.get_input_filename()),
        )
        logger.info(
            'Found outcomes file at %s',
            self.dataset_settings.outcomes_file,
        )
        logger.info(
            'Will write output to %s',
            self.jobs_paths.output_path,
        )

    def _calculate(self):
        try:
            markers = self.dataset_design.get_elementary_phenotype_names()
            for distance_type in DistanceTypes:
                for marker in markers:
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

    def save_transition_probability_values(self, values=None, distance_type_str: str=None, temporal_offset=None, marker:str=None):
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

    def start_post_jobs_step(self):
        integrator = DiffusionAnalysisIntegrator(
            jobs_paths = self.jobs_paths,
            dataset_settings = self.dataset_settings,
            computational_design = self.computational_design,
        )
        integrator.calculate()
