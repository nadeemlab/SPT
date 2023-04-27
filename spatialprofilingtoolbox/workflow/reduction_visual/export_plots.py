"""
Convenience uploader of feature data into SPT database tables that comprise
a sparse representation of the features. Abstracts (wraps) the actual SQL
queries.
"""
import importlib.resources

import pandas as pd

from spatialprofilingtoolbox.db.source_file_parser_interface import SourceToADIParser
from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

class PlotUploader(SourceToADIParser, DatabaseConnectionMaker):
    """
    todo: Adapted from ADIFeaturesUploader (spatialprofilingtoolbox/workflow/common/export_features.py). Should inherit?
    Upload string representations of scatter plots to table 'visualization_plots'.
    """
    feature_value_identifier: int

    def __init__(self,
                 database_config_file,
                 data_analysis_study,
                 derivation_method,
                 **kwargs):
        # todo: "database schema" for the new table stored in a separate file for compatibility with SourceToADIParser
        with importlib.resources.files('spatialprofilingtoolbox').joinpath('workflow').joinpath('assets').joinpath(
                'fields.tsv') as path:
            fields = pd.read_csv(path, sep='\t', na_filter=False)
        SourceToADIParser.__init__(self, fields)
        self.record_feature_specification_template(
            data_analysis_study, derivation_method)
        DatabaseConnectionMaker.__init__(self, database_config_file=database_config_file)

    def record_feature_specification_template(self,
                                              data_analysis_study,
                                              derivation_method,
                                              specifier_number=1):
        self.data_analysis_study = data_analysis_study
        self.derivation_method = derivation_method
        self.specifier_number = specifier_number
        self.insert_query = self.generate_basic_insert_query('visualization_plots')
        self.feature_values = []

    def __exit__(self, exception_type, exception_value, traceback):
        if self.connection:
            self.upload()
            self.connection.close()

    # todo: arguably primary study is the sample identifier
    def stage_feature_value(self, specifiers, primary_study, value):
        # self.validate_specifiers(specifiers)
        logger.debug(f"Staging values for target {specifiers}")
        self.feature_values.append([specifiers, primary_study, value])

    def validate_specifiers(self, specifiers):
        if len(specifiers) != self.specifier_number:
            message = \
                f'Feature specified by "{specifiers}", but should only have ' \
                f'{self.specifier_number} specifiers.'
            logger.error(message)
            raise ValueError(message)

    def upload(self):
        # if self.check_nothing_to_upload():
        #     return
        # if self.check_exact_feature_values_already_present():
        #     return
        #self.test_chemical_species_existence()
        cursor = self.get_connection().cursor()
        self.get_feature_value_next_identifier(cursor=cursor)

        logger.info(f'Inserting {len(self.feature_values)} feature "%s" for study "%s".',
                    self.derivation_method, self.data_analysis_study)
        for target_identifier, study_name, plot_string in self.feature_values:
            self.insert_plot_value(cursor, analysis_study_name=self.data_analysis_study,
                                   target_identifier=target_identifier, plot_value=plot_string)
            logger.debug(f'Inserted plot for target {target_identifier}.')

        self.get_connection().commit()
        cursor.close()

    def check_nothing_to_upload(self):
        if len(self.feature_values) == 0:
            logger.info('No feature values given to be uploaded.')
            return True
        return False

    def check_exact_feature_values_already_present(self):
        count = self.count_known_feature_values_this_study()
        if count == len(self.feature_values):
            logger.info(
                'Exactly %s feature values already associated with study "%s" of '
                'description "%s". This is the correct number; skipping upload '
                'without error.',
                count, self.data_analysis_study, self.derivation_method)
            return True
        if count > 0:
            message = f'Already have {count} features associated with study ' \
                f'"{self.data_analysis_study}" of description "{self.derivation_method}". ' \
                'Skipping upload with error.'
            logger.error(message)
            raise ValueError(message)
        if count == 0:
            logger.info(
                'No feature values yet associated with study "%s" of description "%s". '
                'Proceeding with upload.',
                self.data_analysis_study, self.derivation_method)
            return False
        return None

    def count_known_feature_values_this_study(self):
        cursor = self.get_connection().cursor()
        count_query = '''
        SELECT COUNT(*)
        FROM visualization_plots vp
        JOIN study_component sc ON vp.study = sc.component_study 
        WHERE sc.primary_study = %s AND fs.derivation_method = %s
        ;
        '''
        # todo: fix workaround to avoid duplicate plots - ignore timestamp
        prname = self.data_analysis_study.split(':', 1)[0].strip()
        cursor.execute(
            count_query, (prname, self.derivation_method))
        rows = cursor.fetchall()
        count = rows[0][0]
        cursor.close()
        return count

    # def test_chemical_species_existence(self):
    #     species_ids = self.get_species_identifiers()
    #     unknown_species = set(row[1] for row in self.feature_values).difference(species_ids)
    #     if len(unknown_species) > 0:
    #         logger.warning('Feature values refer to %s unknown species: %s', len(
    #             unknown_species), str(list(unknown_species)))
    #
    # def get_species_identifiers(self):
    #     cursor = self.get_connection().cursor()
    #     cursor.execute('SELECT identifier FROM chemical_species;')
    #     rows = cursor.fetchall()
    #     species_ids = [row[0] for row in rows]
    #     cursor.close()
    #     return species_ids

    def test_study_existence(self):
        cursor = self.get_connection().cursor()
        cursor.execute('SELECT name FROM data_analysis_study;')
        rows = cursor.fetchall()
        names = [row[0] for row in rows]
        cursor.close()
        if not self.data_analysis_study in names:
            message = f'Data analysis study "{self.data_analysis_study}" does not exist.'
            logger.error(message)
            raise ValueError(message)

    def get_feature_value_next_identifier(self, cursor):
        next_identifier = self.get_next_integer_identifier('visualization_plots', cursor)
        self.feature_value_identifier = next_identifier

    def request_new_feature_value_identifier(self):
        identifier = self.feature_value_identifier
        self.feature_value_identifier = self.feature_value_identifier + 1
        return identifier

    def insert_plot_value(self, cursor, analysis_study_name, target_identifier, plot_value):
        identifier = self.request_new_feature_value_identifier()
        logger.debug(
            f"About to insert values {identifier}, {target_identifier}, {analysis_study_name},"
            f" {plot_value[:10]} into '{self.insert_query}'")

        cursor.execute(
            self.insert_query,
            (identifier, target_identifier, analysis_study_name, plot_value),
        )
