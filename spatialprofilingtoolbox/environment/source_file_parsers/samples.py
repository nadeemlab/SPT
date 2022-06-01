import re

import pandas as pd
import psycopg2
from psycopg2 import sql

from .parser import SourceFileSemanticParser
from ..logging.log_formats import colorized_logger
logger = colorized_logger(__name__)


class SamplesParser(SourceFileSemanticParser):
    def __init__(self, **kwargs):
        super(SamplesParser, self).__init__(**kwargs)

    def get_unique_value(self, dataframe, column):
        handles = sorted(list(set(dataframe[column]).difference([''])))
        if len(handles) == 0:
            message = 'No "%s" values are supplied with the file manifest for this run.' % column
            logger.error(message)
            raise ValueError(message)
        if len(handles) > 1:
            message = 'Multiple "%s" values were supplied with the file manifest for this run. Using "%s".' % (column, project_handles[0])
            logger.warning(message)
        return handles[0]

    def normalize(self, name):
        return re.sub('[ \-]', '_', name).lower()

    def retrieve_record_counts(self, cursor, fields):
        record_counts = {}
        tablenames = sorted(list(set(fields['Table'])))
        for table in tablenames:
            query = sql.SQL('SELECT COUNT(*) FROM {} ;').format(sql.Identifier(self.normalize(table)))
            cursor.execute(query)
            rows = cursor.fetchall()
            record_counts[table] = rows[0][0]
        return record_counts

    def cache_all_record_counts(self, connection, fields):
        cursor = connection.cursor()
        self.record_counts = self.retrieve_record_counts(cursor, fields)
        cursor.close()

    def report_record_count_changes(self, connection, fields):
        cursor = connection.cursor()
        current_counts = self.retrieve_record_counts(cursor, fields)
        changes = {
            table: current_counts[table] - self.record_counts[table]
        }
        cursor.close()
        logger.debug('Record count changes:')
        for table, difference in changes.items():
            sign = '+' if difference >= 0 else '-'
            absolute_difference = difference if difference > 0 else -1*difference
            logger.debug('%s%s %s', sign, difference, table)

    def parse(self, connection, fields, samples_file, age_at_specimen_collection, file_manifest_file):
        """
        Retrieve the samples information and parse records for:
        - specimen collection study
        - specimen collection process
        - histology assessment process
        """
        self.cache_all_record_counts(connection, fields)
        file_metadata = pd.read_csv(file_manifest_file, sep='\t')
        samples = pd.read_csv(samples_file, sep='\t', dtype=str)

        project_handle = self.get_unique_value(file_metadata, 'Project ID')
        collection_study = project_handle + ' - specimen collection'
        extraction_method = self.get_unique_value(samples, 'Extraction method')
        preservation_method = self.get_unique_value(samples, 'Preservation method')
        storage_location = self.get_unique_value(samples, 'Storage location')

        cursor = connection.cursor()
        cursor.execute(
            self.generate_basic_insert_query('specimen_collection_study', fields),
            (collection_study, extraction_method, preservation_method, storage_location, '', ''),
        )

        for i, sample in samples.iterrows():
            record = self.create_specimen_collection_process_record(
                sample,
                age_at_specimen_collection,
                collection_study,
            )
            cursor.execute(
                self.generate_basic_insert_query('specimen_collection_process', fields),
                record,
            )

        for i, sample in samples.iterrows():
            record = self.create_histology_assessment_process_record(sample)
            cursor.execute(
                self.generate_basic_insert_query('histology_assessment_process', fields),
                record,
            )

        logger.info('Parsed records for %s specimens.', samples.shape[0])
        connection.commit()
        cursor.close()
        self.report_record_count_changes(connection, fields)

    def create_specimen_collection_process_record(self, sample, age_at_specimen_collection, collection_study):
        return (
            sample['Sample ID'],
            sample['Source subject'],
            sample['Source site'],
            age_at_specimen_collection[sample['Source subject']],
            sample['Extraction date'],
            collection_study,
        )

    def create_histology_assessment_process_record(self, sample):
        return (
            sample['Sample ID'],
            sample['Assay'],
            sample['Assessment'],
            '',
            '',
        )
