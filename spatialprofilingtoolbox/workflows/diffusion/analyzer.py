import os
from os.path import join, dirname
import re
import sqlite3
import pandas as pd

from ...environment.single_job_analyzer import SingleJobAnalyzer
from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.log_formats import colorized_logger
from .integrator import DiffusionAnalysisIntegrator
from .computational_design import DiffusionDesign
from .core import DiffusionCalculator, DistanceTypes

logger = colorized_logger(__name__)


class DiffusionAnalyzer(SingleJobAnalyzer):
    def __init__(self,
        regional_compartment: str='nontumor',
        **kwargs,
    ):
        """
        :param regional_compartment: The regional compartment (in the sense of
        ``diffusion.job_generator.get_regional_compartments()``) in which reside
        the cells to be considered by this job.
        :type regional_compartment: str
        """
        super(DiffusionAnalyzer, self).__init__(**kwargs)
        self.regional_compartment = regional_compartment
        self.retrieve_input_filename()
        input_filename = self.get_input_filename()
        self.input_filename = input_filename

    def _calculate(self):
        try:
            fovs = cut_by_header(self.input_filename, column=self.dataset_design.get_FOV_column())
            number_fovs = len(sorted(list(set(fovs))))
            for fov_index in range(1, 1+number_fovs):
                self.fov_index = fov_index
                self.calculator = DiffusionCalculator(
                    input_filename = self.input_filename,
                    fov_index = fov_index,
                    regional_compartment = self.regional_compartment,
                    dataset_design = self.dataset_design,
                    computational_design = self.computational_design,
                )

                markers = self.dataset_design.get_elementary_phenotype_names()
                for distance_type in DistanceTypes:
                    if distance_type != DistanceTypes.EUCLIDEAN:
                        continue
                    for marker in markers:
                        if not marker in ['DAPI', 'CK']: # Factor this out!
                            self.dispatch_diffusion_calculation(distance_type, marker)
                    logger.debug('Completed analysis %s, %s, (%s)',
                        self.get_job_descriptor(),
                        fov_index,
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

def cut_by_header(input_filename, delimiter=',', column: str=None):
    """
    This function attempts to emulate the speed and function of the UNIX-style
    ``cut`` command for a single field. The implementation here uses Pandas to read
    the whole table into memory; a future implementation may avert this.
    Args:
        input_filename (str):
            Input CSV-style file.
        delimiter (str):
            Delimiter character.
        column (str):
            The header value for the column you want returned.
    Returns:
        values (list):
            The single column of values.
    """
    if not column:
        logger.error('"column" is a mandatory argument.')
        raise ValueError
    df = pd.read_csv(input_filename, delimiter=delimiter)
    return list(df[column])
