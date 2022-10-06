
import pandas as pd

from ...db.source_file_parser_interface import SourceToADIParser
from ...standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)


class SubjectsParser(SourceToADIParser):
    def __init__(self, **kwargs):
        super(SubjectsParser, self).__init__(**kwargs)

    def parse(self, connection, fields, subjects_file):
        """
        Retrieve SUBJECT data in the same way that the main workflows do, and parse
        records for:
        - subject
        - diagnosis
        """
        cursor = connection.cursor()

        def create_subject_record(subject_id, sex):
            return (subject_id, '', sex, '', '', '')

        def create_diagnosis_record(subject_id, assay, result):
            return (subject_id, assay, result, '', '')

        logger.debug('Considering %s', subjects_file)
        subjects = pd.read_csv(subjects_file, sep='\t', na_filter=False, dtype=str)
        logger.info('Saving %s subject records.', subjects.shape[0])
        for i, row in subjects.iterrows():
            cursor.execute(
                self.generate_basic_insert_query('subject', fields),
                create_subject_record(row['Subject ID'], row['Sex']),
            )
        logger.info('Saving %s diagnosis records.', subjects.shape[0])
        for i, row in subjects.iterrows():
            diagnosis_record = create_diagnosis_record(
                row['Subject ID'],
                row['Diagnosed condition'],
                row['Diagnosis'],
            )
            cursor.execute(
                self.generate_basic_insert_query('diagnosis', fields),
                diagnosis_record,
            )
        connection.commit()
        cursor.close()

        age_at_specimen_collection = {
            row['Subject ID'] : row['Age at specimen collection']
            for i, row in subjects.iterrows()
        }
        return age_at_specimen_collection
