
import pandas as pd

from .parser import SourceFileSemanticParser
from ..logging.log_formats import colorized_logger
logger = colorized_logger(__name__)


class SubjectsParser(SourceFileSemanticParser):
    def __init__(self, **kwargs):
        super(SubjectsParser, self).__init__(**kwargs)

    def parse(self, connection, fields, subjects_file, outcomes_file):
        """
        Retrieve SUBJECT data in the same way that the main workflows do, and parse
        records for:
        - subject
        - diagnosis
        """
        cursor = connection.cursor()


        def create_subject_record(sample_id):
            return (sample_id, '', '', '', '', '')

        def create_diagnosis_record(sample_id, result, column_name):
            return (sample_id, column_name, result, '', '')

        logger.debug('Considering %s', outcomes_file)
        outcomes = pd.read_csv(outcomes_file, sep='\t', na_filter=False, dtype=str)
        sample_ids = sorted(list(set(outcomes['Sample ID'])))
        logger.info('Saving %s subject records.', len(sample_ids))
        for sample_id in sample_ids:
            cursor.execute(
                self.generate_basic_insert_query('subject', fields),
                create_subject_record(sample_id),
            )
        logger.info('Saving %s diagnosis records.', outcomes.shape[0])
        for i, row in outcomes.iterrows():
            diagnosis_record = create_diagnosis_record(
                row['Sample ID'],
                row[outcomes.columns[1]],
                outcomes.columns[1],
            )
            cursor.execute(
                self.generate_basic_insert_query('diagnosis', fields),
                diagnosis_record,
            )
        connection.commit()
        cursor.close()
