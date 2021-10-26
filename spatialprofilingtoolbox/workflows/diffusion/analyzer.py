import os
from os.path import join, dirname
import re
import sqlite3

from ...environment.single_job_analyzer import SingleJobAnalyzer
from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.log_formats import colorized_logger
from .integrator import DiffusionAnalysisIntegrator
from .computational_design import DiffusionDesign
from .core import DiffusionCalculator, DistanceTypes

logger = colorized_logger(__name__)


class DiffusionAnalyzer(SingleJobAnalyzer):
    def __init__(self,
        fov_index: int=None,
        regional_compartment: str='nontumor',
        **kwargs,
    ):
        """
        :param fov_index: The integer index of the field of view to be considered by
        this job.
        :type fov_index: int

        :param regional_compartment: The regional compartment (in the sense of
        ``diffusion.job_generator.get_regional_compartments()``) in which reside
        the cells to be considered by this job.
        :type regional_compartment: str
        """
        super(DiffusionAnalyzer, self).__init__(**kwargs)
        self.regional_compartment = regional_compartment
        self.retrieve_input_filename()
        self.fov_index = fov_index
        self.calculator = DiffusionCalculator(
            input_filename = self.get_input_filename(),
            fov_index = fov_index,
            regional_compartment = regional_compartment,
            dataset_design = self.dataset_design,
            computational_design = self.computational_design,
        )

    def _calculate(self):
        try:
            markers = self.dataset_design.get_elementary_phenotype_names()
            for distance_type in DistanceTypes:
                if distance_type != DistanceTypes.EUCLIDEAN:
                    continue
                for marker in markers:
                    if not marker in ['DAPI', 'CK']: # Factor this out!
                        self.dispatch_diffusion_calculation(distance_type, marker)
                logger.debug('Completed analysis %s (%s)',
                    self.get_job_descriptor(),
                    distance_type.name,
                )
        except Exception as e:
            logger.error('Job failed: %s', e)
            raise e

    def dispatch_diffusion_calculation(self, distance_type, marker):
        """
        Delegates the main job calculation to ``diffusion.core``.

        :param distance_type: Type of distance considered as underlying point-set
            metric for the purposes of the diffusion calculation.
        :type distace_type: DistanceTypes
        
        :param marker: The elementary phenotype name whose positive cells are to be
            considered.
        :type marker: str
        """
        self.calculator.calculate_diffusion(distance_type, marker)

        values = self.calculator.get_values('diffusion kernel')
        if values is not None:
            self.save_diffusion_distance_values(
                values=values,
                distance_type_str=distance_type.name,
                marker=marker,
            )

        for t in self.calculator.get_temporal_offsets():
            values = self.calculator.get_values(t)
            self.save_diffusion_distance_values(
                values=values,
                distance_type_str=distance_type.name,
                temporal_offset=t,
                marker=marker,
            )

    def save_diffusion_distance_values(self,
        values=None,
        distance_type_str: str=None,
        temporal_offset=None,
        marker:str=None,
    ):
        """
        Exports results from ``diffusion.core`` calculation.

        :param values: List of numeric diffusion distance values to save.
        :type values: list

        :param distance_type_str: The distance type (point-set metric) for the context
        in which the values were computed.
        :type distance_type_str: str

        :param temporal_offset: The time duration for running the Markov chain process.
        :type temporal_offset: float

        :param marker: The elementary phenotype name for the context in which the
            values were computed.
        :type marker: str
        """
        if temporal_offset is None:
            temporal_offset = 'NULL'
        uri = self.computational_design.get_database_uri()
        with WaitingDatabaseContextManager(uri) as m:
            for value in values:
                m.execute(' '.join([
                    'INSERT INTO',
                    self.computational_design.get_diffusion_distances_table_name(),
                    '(' + ', '.join(self.computational_design.get_probabilities_table_header()) + ')',
                    'VALUES',
                    '(' + str(value) +', "' + distance_type_str + '", "' + str(self.get_job_descriptor()) + '", "' + str(self.get_sample_identifier()) + '", ' + str(temporal_offset) + ', ' + '"' + marker + '"' + ' ' + ');'
                ]))
            m.commit()

    def get_job_descriptor(self):
        return 'file ID %s and FOV index %s' % (
            self.input_file_identifier,
            self.fov_index,
        )

    def initialize_intermediate_database(self):
        """
        The diffusion workflow uses a pipeline-specific database to store its
        intermediate outputs. This method initializes this database's tables.
        """
        probabilities_header = self.computational_design.get_probabilities_table_header()

        connection = sqlite3.connect(self.computational_design.get_database_uri())
        cursor = connection.cursor()
        table_name = self.computational_design.get_diffusion_distances_table_name()
        # Migrate below to documented schema in line with other workflows
        cmd = ' '.join([
            'CREATE TABLE IF NOT EXISTS',
            table_name,
            '(',
            'id INTEGER PRIMARY KEY AUTOINCREMENT,',
            probabilities_header[0] + ' NUMERIC,',
            probabilities_header[1] + ' VARCHAR(25),',
            probabilities_header[2] + ' TEXT,',
            probabilities_header[3] + ' TEXT,',
            probabilities_header[4] + ' NUMERIC,',
            probabilities_header[5] + ' TEXT',
            ');',
        ])
        cursor.execute(cmd)

        cursor.close()
        connection.commit()
        connection.close()
