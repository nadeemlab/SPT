import importlib.resources
import re
import os
from os.path import getsize

import psycopg2
import pandas as pd

from .log_formats import colorized_logger
logger = colorized_logger(__name__)

from .file_io import get_input_filenames_by_data_type
from .file_io import get_input_filename_by_identifier
from .file_io import get_outcomes_files
from .file_io import compute_sha256


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
        """
        Retrieve the set of cell manifests (i.e. just the "metadata" for each source
        file), and parse records for:
        - specimen collection study
        - specimen collection process
        - specimen measurement study
        - specimen data measurement process
        - data file
        """
        file_metadata = pd.read_csv(self.dataset_settings.file_manifest_file, sep='\t')
        halo_data_type = 'HALO software cell manifest'
        cell_manifests = file_metadata[
            file_metadata['Data type'] == halo_data_type
        ]

        def create_specimen_collection_process_record(specimen, source, study):
            return (specimen, source, '', '', '', study)

        def create_specimen_data_measurement_process_record(
            identifier,
            specimen,
            study,
        ):
            return (identifier, specimen, '', '', study)

        def create_data_file_record(
            sha256_hash,
            file_name,
            file_format,
            contents_format,
            size,
            source_generation_process,
        ):
            return (
                sha256_hash,
                file_name,
                file_format,
                contents_format,
                size,
                source_generation_process,
            )

        project_handles = sorted(list(set(file_metadata['Project ID']).difference([''])))
        if len(project_handles) == 0:
            message = 'No "Project ID" values are supplied with the file manifest for this run.'
            logger.error(message)
            raise ValueError(message)
        if len(project_handles) > 1:
            message = 'Multiple "Project ID" values were supplied with the file manifest for this run. Using "%s".' % project_handles[0]
            logger.warning(message)
        project_handle = project_handles[0]
        collection_study = project_handle + ' - specimen collection'
        measurement_study = project_handle + ' - measurement'

        cursor = self.connection.cursor()
        cursor.execute(
            self.generate_basic_insert_query('specimen_collection_study'),
            (collection_study, '', '', '', '', ''),
        )
        cursor.execute(
            self.generate_basic_insert_query('specimen_measurement_study'),
            (measurement_study, 'Multiplexed imaging', '', 'HALO', '', ''),
        )

        for i, cell_manifest in cell_manifests.iterrows():
            logger.debug('Considering file "%s" .', cell_manifest['File ID'])
            subject_id = cell_manifest['Sample ID']
            subspecimen_identifier = subject_id + ' subspecimen'
            cursor.execute(
                self.generate_basic_insert_query('specimen_collection_process'),
                create_specimen_collection_process_record(
                    subspecimen_identifier,
                    subject_id,
                    collection_study,
                ),
            )
            filename = get_input_filename_by_identifier(
                dataset_settings = self.dataset_settings,
                input_file_identifier = cell_manifest['File ID'],
            )
            sha256_hash = compute_sha256(filename)

            if 'SHA256' in cell_manifests.columns:
                if sha256_hash != cell_manifest['SHA256']:
                    logger.warning(
                        'Computed hash "%s" does not match hash supplied in file manifest, "%s", for file "%s".',
                        sha256_hash,
                        cell_manifest['SHA256'],
                        cell_manifest['File ID'],
                    )

            measurement_process_identifier = sha256_hash + ' measurement'
            cursor.execute(
                self.generate_basic_insert_query('specimen_data_measurement_process'),
                create_specimen_data_measurement_process_record(
                    measurement_process_identifier,
                    subspecimen_identifier,
                    measurement_study,
                ),
            )
            match = re.search('\.([a-zA-Z0-9]{1,8})$', cell_manifest['File name'])
            if match:
                file_format = match.groups(1)[0].upper()
            else:
                file_format = ''
            size = getsize(filename)
            cursor.execute(
                self.generate_basic_insert_query('data_file'),
                create_data_file_record(
                    sha256_hash,
                    cell_manifest['File name'],
                    file_format,
                    halo_data_type,
                    size,
                    measurement_process_identifier,
                ),
            )
        logger.info('Parsed records for %s cell manifests.', cell_manifests.shape[0])
        self.connection.commit()
        cursor.close()

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

