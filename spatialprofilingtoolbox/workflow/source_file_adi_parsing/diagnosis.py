
import pandas as pd

from ...db.source_file_parser_interface import SourceToADIParser
from ...standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)


class DiagnosisParser(SourceToADIParser):
    def __init__(self, **kwargs):
        super(DiagnosisParser, self).__init__(**kwargs)

    def parse(self, connection, fields, diagnosis_file):
        cursor = connection.cursor()

        logger.debug('Considering %s', diagnosis_file)
        diagnoses = pd.read_csv(diagnosis_file, sep='\t', na_filter=False, dtype=str)
        logger.info('Saving %s diagnosis records.', diagnoses.shape[0])
        for i, row in diagnoses.iterrows():
            diagnosis_record = (
                row['Subject of diagnosis'],
                row['Diagnosed condition'],
                row['Diagnosis'],
                row['Date of diagnosis'],
            )
            cursor.execute(
                self.generate_basic_insert_query('diagnosis', fields),
                diagnosis_record,
            )
        connection.commit()
        cursor.close()
