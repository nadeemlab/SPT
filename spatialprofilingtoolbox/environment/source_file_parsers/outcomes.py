import os
from os.path import join

import pandas as pd

from ..file_io import get_input_filenames_by_data_type
from .parser import SourceFileSemanticParser
from ..logging.log_formats import colorized_logger
logger = colorized_logger(__name__)


class OutcomesParser(SourceFileSemanticParser):
    def __init__(self, **kwargs):
        super(OutcomesParser, self).__init__(**kwargs)

    def parse(self, connection, fields, dataset_design):
        """
        Retrieve outcome data in the same way that the main workflows do, and parse
        records for:
        - subject
        - diagnosis
        """
        cursor = connection.cursor()

        def create_subject_record(sample_id):
            return (sample_id, '', '', '', '', '')

        def create_diagnosis_record(sample_id, result, column_name):
            return (sample_id, column_name, result, '', '')

        outcomes_files = get_input_filenames_by_data_type(
            data_type='Outcome',
            file_manifest_filename=self.file_manifest_file,
        )
        for outcomes_file in outcomes_files:
            logger.debug('Considering %s', outcomes_file)
            outcomes = pd.read_csv(join(self.input_path, outcomes_file), sep='\t', na_filter=False)
            sample_ids = sorted(list(set(outcomes['Sample ID'])))
            logger.info('Saving %s subject records.', len(sample_ids))
            for sample_id in sample_ids:
                cursor.execute(
                    self.generate_basic_insert_query('subject', fields),
                    create_subject_record(sample_id),
                )
            logger.info('Saving %s diagnosis records.', outcomes.shape[0])
            for i, row in outcomes.iterrows():
                cursor.execute(
                    self.generate_basic_insert_query('diagnosis', fields),
                    create_diagnosis_record(
                        row['Sample ID'],
                        row[outcomes.columns[1]],
                        outcomes.columns[1]
                    ),
                )
        connection.commit()
        cursor.close()
