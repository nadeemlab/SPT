
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

        logger.debug('Considering %s', subjects_file)
        subjects = pd.read_csv(subjects_file, sep='\t', na_filter=False, dtype=str)
        logger.info('Saving %s subject records.', subjects.shape[0])
        for i, row in subjects.iterrows():
            cursor.execute(
                self.generate_basic_insert_query('subject', fields),
                create_subject_record(row['Subject ID'], row['Sex']),
            )
        connection.commit()
        cursor.close()
