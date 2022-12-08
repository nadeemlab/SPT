
import pandas as pd

from ...db.source_file_parser_interface import SourceToADIParser
from ...standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)


class InterventionsParser(SourceToADIParser):
    def __init__(self, **kwargs):
        super(InterventionsParser, self).__init__(**kwargs)

    def parse(self, connection, fields, diagnosis_file):
        cursor = connection.cursor()

        logger.debug('Considering %s', intervention_file)
        interventions = pd.read_csv(intervention_file, sep='\t', na_filter=False, dtype=str)
        logger.info('Saving %s intervention records.', interventions.shape[0])
        for i, row in interventions.iterrows():
            intervention_record = (
                row['Subject of intervention'],
                row['Intervention'],
                row['Date of intervention'],
            )
            cursor.execute(
                self.generate_basic_insert_query('intervention', fields),
                intervention_record,
            )
        connection.commit()
        cursor.close()
