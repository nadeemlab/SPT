import importlib.resources
import re

import psycopg2
import pandas as pd

from .log_formats import colorized_logger
logger = colorized_logger(__name__)

from .file_io import get_input_filenames_by_data_type
from .file_io import get_outcomes_files


class DataSkimmer:
    def __init__(self, endpoint, user, password, dataset_settings, dataset_design):
        try:
            self.connection = psycopg2.connect(
                dbname='pathstudies',
                user=user,
                password=password,
                host=endpoint,
            )
        except psycopg2.Error as e:
            logger.error('Failed to connect to database: %s', e.pgerror)
        self.dataset_settings = dataset_settings
        self.dataset_design = dataset_design

        with importlib.resources.path('spatialprofilingtoolbox', 'fields.tsv') as path:
            self.fields = pd.read_csv(path, sep='\t', na_filter=False)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.connection.close()

    def skim_initial_data(self):
        self.parse_outcomes()
        self.parse_cell_manifest_set()
        self.parse_channels_and_phenotypes()
        self.parse_cell_manifests()

    def normalize(self, string):
        string = re.sub('[ \-]', '_', string)
        string = string.lower()
        return string

    def generate_basic_insert_query(self, tablename):
        fields = [
            field
            for i, field in self.fields.iterrows()
            if self.normalize(field['Table']) == self.normalize(tablename)
        ]
        fields_sorted = sorted(fields, key=lambda field: int(field['Ordinality']))
        query = (
            'INSERT INTO ' + tablename + ' (' + ', '.join([field['Name'] for field in fields_sorted]) + ') '
            'VALUES (' + ', '.join(['%s']*len(fields_sorted)) + ') '
            'ON CONFLICT DO NOTHING;'
        )
        return query

    def parse_outcomes(self):
        """
        Retrieve outcome data in the same way that the main workflows do, and parse
        records for:
        - subject
        - diagnosis
        """
        cursor = self.connection.cursor()

        def create_subject_record(sample_id):
            return (sample_id, '', '', '', '', '')

        def create_diagnosis_record(sample_id, result, column_name):
            return (sample_id, column_name, result, '', '')

        for outcomes_file in get_outcomes_files(self.dataset_settings):
            logger.debug('Considering %s', outcomes_file)
            outcomes = pd.read_csv(outcomes_file, sep='\t', na_filter=False)
            sample_ids = sorted(list(set(outcomes['Sample ID'])))
            logger.info('Saving %s subject records.', len(sample_ids))
            for sample_id in sample_ids:
                cursor.execute(
                    self.generate_basic_insert_query('subject'),
                    create_subject_record(sample_id),
                )
            logger.info('Saving %s diagnosis records.', outcomes.shape[0])
            for i, row in outcomes.iterrows():
                cursor.execute(
                    self.generate_basic_insert_query('diagnosis'),
                    create_diagnosis_record(
                        row['Sample ID'],
                        row[outcomes.columns[1]],
                        outcomes.columns[1]
                    ),
                )
        self.connection.commit()
        cursor.close()

    def parse_cell_manifest_set(self):
        pass
        # specimen collection study
        # specimen collection process
        # specimen measurement study
        # specimen data measurement process
        # data file

    def parse_channels_and_phenotypes(self):
        pass
        # chemical species
        # cell phenotype
        # cell phenotype criterion
        # biological marking system
        # data analysis study

    def parse_cell_manifests(self):
        pass
        # histological structure identification
        # histological structure
        # shape file
        # expression quantification

    def skim_final_data(self, ):
        pass
        # two cohort feature assocation test
        # feature specification
        # feaure specifier
        # diagnostic selection criterion

