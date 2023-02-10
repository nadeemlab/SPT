"""
The integration phase of the proximity workflow. Performs statistical tests.
"""
from typing import Optional
import datetime
import re
import pickle
from math import isnan

from spatialprofilingtoolbox.workflow.component_interfaces.integrator import Integrator
from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.workflow.common.export_features import ADIFeaturesUploader
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class PhenotypeProximityAnalysisIntegrator(Integrator):
    """
    The main class of the integration phase.
    """
    def __init__(self,
                 study_name: str='',
                 database_config_file: Optional[str] = None,
                 **kwargs # pylint: disable=unused-argument
                 ):
        self.study_name = study_name
        self.database_config_file = database_config_file

    def calculate(self, core_computation_results_files=None, **kwargs):
        """
        Performs statistical comparison tests and writes results to file.
        """
        logger.info('(Should do integration phase.)')
        for filename in core_computation_results_files:
            logger.info('Will consider file %s', filename)
        data_analysis_study = self.insert_new_data_analysis_study()
        self.export_feature_values(core_computation_results_files, data_analysis_study)

    def insert_new_data_analysis_study(self):
        timestring = str(datetime.datetime.now())
        name = self.study_name + f'{self.study_name} : proximity calculation : {timestring}'
        with DatabaseConnectionMaker(self.database_config_file) as dcm:
            connection = dcm.get_connection()
            cursor = connection.cursor()
            cursor.execute('''
            INSERT INTO data_analysis_study(name)
            VALUES (%s) ;
            INSERT INTO study_component(primary_study, component_study)
            VALUES (%s, %s) ;
            ''', (name, self.study_name, name))
            cursor.close()
            connection.commit()
        return name

    def export_feature_values(self, core_computation_results_files, data_analysis_study):
        with ADIFeaturesUploader(
            database_config_file=self.database_config_file,
            data_analysis_study=data_analysis_study,
            derivation_method=self.describe_feature_derivation_method(),
            specifier_number=3,
        ) as feature_uploader:
            self.send_features_to_uploader(feature_uploader, core_computation_results_files)

    def send_features_to_uploader(self, feature_uploader, core_computation_results_files):
        for results_file in core_computation_results_files:
            with open(results_file, 'rb') as file:
                feature_values, channel_symbols_by_column_name, sample_identifier= pickle.load(file)
            for _, row in feature_values.iterrows():
                specifiers = (self.phenotype_identifier_lookup(row['Phenotype 1'],
                              channel_symbols_by_column_name),
                              self.phenotype_identifier_lookup(row['Phenotype 2'],
                              channel_symbols_by_column_name),
                              row['Pixel radius'])
                value = row['Proximity']
                if self.validate_value(value):
                    feature_uploader.stage_feature_value(specifiers, sample_identifier, value)

    def validate_value(self, value):
        if (not isinstance(value, float)) and (not isinstance(value, int)):
            return False
        if isnan(value):
            return False
        return True

    def phenotype_identifier_lookup(self, handle, channel_symbols_by_column_name):
        if re.match(r'^\d+$', handle):
            return f'cell_phenotype {handle}'
        if re.match(r'^F\d+$', handle):
            channel_symbol = channel_symbols_by_column_name[handle]
            return channel_symbol
        raise ValueError(f'Did not understand meaning of specifier: {handle}')

    def describe_feature_derivation_method(self):
        return '''
        For a given cell phenotype (first specifier), the average number of cells of a second phenotype (second specifier) within a specified radius (third specifier).
        '''.lstrip().rstrip()
