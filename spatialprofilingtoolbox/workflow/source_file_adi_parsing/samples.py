
import pandas as pd

from ...db.source_file_parser_interface import SourceToADIParser
from .value_extraction import get_unique_value
from ...standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)


class SamplesParser(SourceToADIParser):
    def __init__(self, **kwargs):
        super(SamplesParser, self).__init__(**kwargs)

    def parse(self, connection, fields, samples_file, age_at_specimen_collection, file_manifest_file):
        """
        Retrieve the samples information and parse records for:
        - specimen collection study
        - specimen collection process
        - histology assessment process
        """
        file_metadata = pd.read_csv(file_manifest_file, sep='\t')
        samples = pd.read_csv(samples_file, sep='\t', dtype=str)

        project_handle = get_unique_value(file_metadata, 'Project ID')
        collection_study = project_handle + ' - specimen collection'
        extraction_method = get_unique_value(samples, 'Extraction method')
        preservation_method = get_unique_value(samples, 'Preservation method')
        storage_location = get_unique_value(samples, 'Storage location')

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
