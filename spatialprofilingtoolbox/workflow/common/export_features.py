import importlib.resources

import pandas as pd

from ...db.source_file_parser_interface import SourceToADIParser
from ...db.database_connection import DatabaseConnectionMaker
from ...standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)


class ADIFeaturesUploader(SourceToADIParser):
    def __init__(self, database_config_file, data_analysis_study, derivation_method, specifier_number, **kwargs):
        super(ADIFeaturesUploader, self).__init__(**kwargs)
        self.record_feature_specification_template(data_analysis_study, derivation_method, specifier_number)
        self.initialize_database_connection(database_config_file)

    def record_feature_specification_template(self, data_analysis_study, derivation_method, specifier_number):
        self.data_analysis_study = data_analysis_study
        self.derivation_method = derivation_method
        self.specifier_number = specifier_number
        with importlib.resources.path('adisinglecell', 'fields.tsv') as path:
            fields = pd.read_csv(path, sep='\t', na_filter=False)
        self.insert_queries = {
            tablename : self.generate_basic_insert_query(tablename, fields)
            for tablename in ['feature_specification', 'feature_specifier', 'quantitative_feature_value']
        }
        self.feature_values = []

    def initialize_database_connection(self, database_config_file):
        dcm = DatabaseConnectionMaker(database_config_file)
        self.connection = dcm.get_connection()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.connection:
            self.upload()
            self.connection.close()

    def stage_feature_value(self, specifiers, subject, value):
        self.validate_specifiers(specifiers)
        self.feature_values.append([specifiers, subject, value])

    def validate_specifiers(self, specifiers):
        if len(specifiers) != self.specifier_number:
            message = 'Feature specified by "%s", but should only have %s specifiers.' % (str(specifiers), str(self.specifier_number))
            logger.error(message)
            raise ValueError(message)

    def upload(self):
        if self.check_nothing_to_upload():
            return
        if self.check_exact_feature_values_already_present():
            return
        self.test_subject_existence()
        self.test_study_existence()

        cursor = self.connection.cursor()
        next_identifier = self.get_next_integer_identifier('feature_specification', cursor)
        specifiers_list = sorted(list(set([row[0] for row in self.feature_values])))
        specifiers_by_id = {
            next_identifier + i : specifiers
            for i, specifiers in enumerate(specifiers_list)
        }

        self.get_feature_value_next_identifier(cursor)
        logger.info('Inserting feature "%s" for study "%s".', self.derivation_method, self.data_analysis_study)
        for feature_identifier, specifiers in specifiers_by_id.items():
            cursor.execute(
                self.insert_queries['feature_specification'],
                (feature_identifier, self.derivation_method, self.data_analysis_study),
            )
            self.insert_specifiers(cursor, specifiers, feature_identifier)
            logger.debug('Inserted feature specification, "%s".', specifiers)
            feature_values = [
                [row[1], row[2]] for row in self.feature_values
                if row[0] == specifiers
            ]
            self.insert_feature_values(cursor, feature_identifier, feature_values)
            logger.debug('Inserted %s feature values.', len(feature_values))

        self.connection.commit()
        cursor.close()

    def check_nothing_to_upload(self):
        if len(self.feature_values) == 0:
            logger.info('No feature values given to be uploaded.')
            return True
        return False

    def check_exact_feature_values_already_present(self):
        count = self.count_known_feature_values_this_study()
        if count == len(self.feature_values):
            tokens = (self.data_analysis_study, self.derivation_method)
            message = 'Exactly %s feature values already associated with study "%s" of description "%s". This is the correct number; skipping upload without error.' % tokens
            logger.info(message)
            return True
        if count > 0:
            tokens = (str(count), self.data_analysis_study, self.derivation_method)
            message = 'Already have %s features associated with study "%s" of description "%s". Skipping upload with error.' % tokens
            logger.error(message)
            raise ValueError(message)
        if count == 0:
            tokens = (self.data_analysis_study, self.derivation_method)
            message = 'No feature values yet associated with study "%s" of description "%s". Proceeding with upload.' % tokens
            logger.info(message)
            return False

    def count_known_feature_values_this_study(self):
        cursor = self.connection.cursor()
        count_query = '''
        SELECT COUNT(*)
        FROM quantitative_feature_value qfv
        JOIN feature_specification fs
        ON fs.identifier = qfv.feature
        WHERE fs.study = %s AND fs.derivation_method = %s
        ;
        '''
        cursor.execute(count_query, (self.data_analysis_study, self.derivation_method))
        rows = cursor.fetchall()
        count = rows[0][0]
        cursor.close()
        return count

    def test_subject_existence(self):
        subject_ids = self.get_subject_identifiers()
        unknown_subjects = set([row[1] for row in self.feature_values]).difference(subject_ids)
        if len(unknown_subjects) > 0:
            logger.warning('Feature values refer to %s unknown subjects: %s', len(unknown_subjects), str(list(unknown_subjects)))

    def get_subject_identifiers(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT identifier FROM subject;')
        rows = cursor.fetchall()
        subject_ids = [row[0] for row in rows]
        cursor.close()
        return subject_ids

    def test_study_existence(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT name FROM data_analysis_study;')
        rows = cursor.fetchall()
        names = [row[0] for row in rows]
        cursor.close()
        if not self.data_analysis_study in names:
            message = 'Data analysis study "%s" does not exist.' % self.data_analysis_study
            logger.error(message)
            raise ValueError(message)

    def get_feature_value_next_identifier(self, cursor):
        next_identifier = self.get_next_integer_identifier('quantitative_feature_value', cursor)
        self.feature_value_identifier = next_identifier

    def request_new_feature_value_identifier(self):
        identifier = self.feature_value_identifier
        self.feature_value_identifier = self.feature_value_identifier + 1
        return identifier

    def insert_specifiers(self, cursor, specifiers, feature_identifier):
        for i, specifier in enumerate(specifiers):
            ordinality = i + 1
            cursor.execute(
                self.insert_queries['feature_specifier'],
                (feature_identifier, specifier, ordinality),
            )

    def insert_feature_values(self, cursor, feature_identifier, feature_values):
        for subject, value in feature_values:
            identifier = self.request_new_feature_value_identifier()
            cursor.execute(
                self.insert_queries['quantitative_feature_value'],
                (identifier, feature_identifier, subject, value),
            )

