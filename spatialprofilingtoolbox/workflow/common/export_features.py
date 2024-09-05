"""Convenience uploader of feature data into SPT database tables that comprise a sparse
representation of the features. Abstracts (wraps) the actual SQL queries.
"""

from typing import cast
from importlib.resources import as_file
from importlib.resources import files
from itertools import product
import re

import pandas as pd  # type: ignore
from psycopg import Connection as PsycopgConnection
from psycopg import Cursor as PsycopgCursor

from spatialprofilingtoolbox.db.describe_features import get_handle
from spatialprofilingtoolbox.db.source_file_parser_interface import SourceToADIParser
from spatialprofilingtoolbox.db.database_connection import ConnectionProvider
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class ADIFeaturesUploader(SourceToADIParser):
    """
    Upload sparse representation of feature values to tables quantitative_feature_value,
    feature_specification, feature_specifier.
    """
    connection_provider: ConnectionProvider
    feature_values: list[tuple[tuple[str, ...], str , float | None]]

    def __init__(self,
        connection: PsycopgConnection,
        data_analysis_study: str,
        derivation_and_number_specifiers,
        impute_zeros: bool = False,
        **kwargs,
    ):
        derivation_method, specifier_number = derivation_and_number_specifiers
        self.impute_zeros = impute_zeros
        with as_file(files('adiscstudies').joinpath('fields.tsv')) as path:
            fields = pd.read_csv(path, sep='\t', na_filter=False)
        SourceToADIParser.__init__(self, fields)
        args = (data_analysis_study, derivation_method, specifier_number)
        self.record_feature_specification_template(*args)
        self.connection_provider = ConnectionProvider(connection)

    def record_feature_specification_template(self,
        data_analysis_study,
        derivation_method,
        specifier_number,
    ):
        self.data_analysis_study = data_analysis_study
        self.derivation_method = derivation_method
        self.specifier_number = specifier_number
        self.insert_queries = {
            tablename: self.generate_basic_insert_query(tablename)
            for tablename in
            ['feature_specification', 'feature_specifier', 'quantitative_feature_value']
        }
        self.feature_values = []

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.connection_provider.is_connected():
            self.upload()

    def stage_feature_value(self, specifiers: tuple[str, ...], subject: str, value: float | None):
        self.validate_specifiers(specifiers)
        self.feature_values.append((specifiers, subject, value))

    def validate_specifiers(self, specifiers):
        if len(specifiers) != self.specifier_number:
            message = \
                f'Feature specified by "{specifiers}", but should only have ' \
                f'{self.specifier_number} specifiers.'
            logger.error(message)
            raise ValueError(message)

    def get_connection(self):
        return self.connection_provider.get_connection()

    def upload(self) -> None:
        if self.check_nothing_to_upload():
            return
        self.test_subject_existence()
        self.test_study_existence()
        if self.impute_zeros:
            self.add_imputed_zero_values()
        cursor = self.get_connection().cursor()
        specifiers_list = sorted(list(set(row[0] for row in self.feature_values)))
        insert_notice = 'Inserting feature "%s" for study "%s".'
        logger.info(insert_notice, self.derivation_method, self.data_analysis_study)
        for specifiers in specifiers_list:
            get_or_create = ADIFeaturesUploader._get_or_create_generic_feature_specification
            feature_identifier, is_new = get_or_create(
                cursor, self.data_analysis_study, specifiers, self.derivation_method
            )
            feature_values = map(
                lambda row: (row[1], row[2]),
                filter(lambda row: row[0] == specifiers, self.feature_values),
            )
            self.insert_feature_values(cursor, feature_identifier, feature_values)
        self.get_connection().commit()
        cursor.close()

    def check_nothing_to_upload(self):
        if len(self.feature_values) == 0:
            logger.info('No feature values given to be uploaded.')
            return True
        return False

    def test_subject_existence(self):
        subject_ids = self.get_subject_identifiers()
        unknown_subjects = set(row[1] for row in self.feature_values).difference(subject_ids)
        number_unknown = len(unknown_subjects)
        if number_unknown > 0:
            unknowns_message = 'Feature values refer to %s unknown subjects: %s'
            subset = list(unknown_subjects)[0:min(10, len(unknown_subjects))]
            logger.warning(unknowns_message, number_unknown, subset)
        else:
            logger.info('All feature value subjects were known "subjects" or "specimens".')

    def get_subject_identifiers(self):
        cursor = self.get_connection().cursor()
        cursor.execute('SELECT identifier FROM subject;')
        rows = cursor.fetchall()
        subject_ids = [row[0] for row in rows]
        cursor.execute('SELECT specimen FROM specimen_collection_process;')
        rows = cursor.fetchall()
        specimen_ids = [row[0] for row in rows]
        cursor.close()
        return subject_ids + specimen_ids

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

    def coordinate_set(self, tuples, coordinate):
        return sorted(list(set(t[coordinate] for t in tuples)))

    def add_imputed_zero_values(self):
        support = [(specifiers, subject) for specifiers, subject, value in self.feature_values]
        known_specifications = self.coordinate_set(support, 0)
        known_subjects = self.coordinate_set(support, 1)
        no_value_cases = []
        for case in product(known_specifications, known_subjects):
            if case not in support:
                no_value_cases.append(case)
        logger.info('Imputed %s zero-value assignments.', len(no_value_cases))
        assignments = [(case[0], case[1], 0) for case in no_value_cases]
        self.feature_values = self.feature_values + assignments

    def insert_feature_values(self, cursor: PsycopgCursor, feature_identifier, feature_values):
        for subject, value in feature_values:
            cursor.execute(
                self.insert_queries['quantitative_feature_value'],
                (feature_identifier, subject, value),
            )

    @classmethod
    def _get_or_create_generic_feature_specification(
        cls,
        cursor: PsycopgCursor,
        data_analysis_study: str,
        specifiers: tuple[str, ...],
        derivation_method: str,
    ) -> tuple[str, bool]:
        specification = cls._get_feature_specification(cursor, specifiers, derivation_method)
        if specification is not None:
            return (specification, False)
        logger.debug(f'Creating feature with specifiers: {specifiers}')
        specification = cls._create_feature_specification(
            cursor, data_analysis_study, specifiers, derivation_method,
        )
        return (specification, True)

    @classmethod
    def _get_feature_specification(cls,
        cursor: PsycopgCursor,
        specifiers: tuple[str, ...],
        derivation_method: str,
    ) -> str | None:
        args = (
            *specifiers,
            derivation_method,
        )
        specifiers_portion = ' AND '.join(
            f"( fs.specifier=%s AND fs.ordinality='{i+1}')"
            for i in range(len(specifiers))
        )
        query = f'''
        SELECT
            fsn.identifier,
            fs.specifier
        FROM feature_specification fsn
        JOIN feature_specifier fs ON fs.feature_specification=fsn.identifier
        WHERE {specifiers_portion} AND fsn.derivation_method=%s
        ;
        '''
        cursor.execute(query, args)
        rows = tuple(cursor.fetchall())
        feature_specifications: dict[str, list[str]] = {row[0]: [] for row in rows}
        matches_list: list[str] = []
        for row in rows:
            feature_specifications[row[0]].append(row[1])
        for key, _specifiers in feature_specifications.items():
            if len(_specifiers) == len(specifiers):
                matches_list.append(key)
        matches = tuple(matches_list)
        if len(matches) == 0:
            return None
        if len(matches) > 1:
            text = 'Multiple features match the selected specification'
            message = f'{text}: {matches} {specifiers}'
            logger.warning(message)
        return matches[0]

    @classmethod
    def _create_feature_specification(cls,
        cursor: PsycopgCursor,
        data_analysis_study: str,
        specifiers: tuple[str, ...],
        derivation_method: str,
    ) -> str:
        Uploader = ADIFeatureSpecificationUploader
        add = Uploader.add_new_feature
        feature_specification = add(specifiers, derivation_method, data_analysis_study, cursor)
        return feature_specification


class ADIFeatureSpecificationUploader:
    """Just upload a new feature specification."""
    @staticmethod
    def add_new_feature(specifiers, derivation_method, data_analysis_study, cursor: PsycopgCursor):
        FSU = ADIFeatureSpecificationUploader
        identifier = FSU.insert_specification(derivation_method, data_analysis_study, cursor)
        FSU.insert_specifiers(identifier, specifiers, cursor)
        return identifier

    @staticmethod
    def ondemand_descriptor():
        return 'ondemand computed features'

    @staticmethod
    def get_data_analysis_study(measurement_study, cursor: PsycopgCursor):
        cursor.execute('''
        SELECT sc.primary_study FROM study_component sc
        WHERE sc.component_study=%s ;
        ''', (measurement_study,))
        study = cursor.fetchall()[0][0]

        cursor.execute('''
        SELECT das.name
        FROM data_analysis_study das
        JOIN study_component sc ON sc.component_study=das.name
        WHERE sc.primary_study=%s ;
        ''', (study,))
        rows = cursor.fetchall()
        ondemand = ADIFeatureSpecificationUploader.ondemand_descriptor()
        names = sorted([row[0] for row in rows if re.search(f'{ondemand}', row[0])])
        if len(names) >= 1:
            return names[0]
        data_analysis_study = ADIFeatureSpecificationUploader.form_ondemand_study_name(study)
        cursor.execute('''
        INSERT INTO data_analysis_study (name) VALUES (%s) ;
        ''', (data_analysis_study,))
        cursor.execute('''
        INSERT INTO study_component (primary_study, component_study) VALUES (%s , %s) ;
        ''', (study, data_analysis_study))
        return data_analysis_study

    @staticmethod
    def form_ondemand_study_name(study: str) -> str:
        ondemand = ADIFeatureSpecificationUploader.ondemand_descriptor()
        return f'{study} - {ondemand}'

    @staticmethod
    def insert_specification(
        derivation_method: str, data_analysis_study: str, cursor: PsycopgCursor,
    ) -> int:
        handle = get_handle(derivation_method)
        query = '''
        INSERT INTO feature_specification (derivation_method, study) VALUES (%s, %s)
        RETURNING identifier ;
        '''
        cursor.execute(query, (derivation_method, data_analysis_study))
        specification = tuple(cursor.fetchall())[0][0]
        logger.debug(f'Inserted specification {specification} ({handle}).')
        return specification

    @staticmethod
    def insert_specifiers(specification, specifiers, cursor: PsycopgCursor):
        many = [(specification, specifier, str(i+1)) for i, specifier in enumerate(specifiers)]
        for entry in many:
            logger.debug('Inserting specifier: %s', entry)
        cursor.executemany('''
        INSERT INTO feature_specifier (feature_specification, specifier, ordinality) VALUES (%s, %s, %s) ;
        ''', [(specification, specifier, str(i+1)) for i, specifier in enumerate(specifiers)])


def add_feature_value(feature_specification, subject, value, cursor: PsycopgCursor):
    cursor.execute('''
    INSERT INTO quantitative_feature_value (feature, subject, value) VALUES (%s, %s, %s) ;
    ''', (feature_specification, subject, value))
