import os
from os.path import join
from os.path import exists
import datetime

import pandas as pd

from .configuration_settings import elementary_phenotypes_file_identifier
from .configuration_settings import composite_phenotypes_file_identifier
from .log_formats import colorized_logger

logger = colorized_logger(__name__)


class JobGenerator:
    """
    An interface for pipeline job generation. Minimally assumes that the pipeline
    acts on input files listed in a file manifest file, itself in a format
    controlled by a relatively precise schema (distributed with the source code of
    this package).
    """
    def __init__(self,
        input_path: str=None,
        file_manifest_file: str=None,
        dataset_design_class=None,
        **kwargs,
    ):
        """
        :param dataset_design_class: Class of design object representing input data set.

        :param input_path: The directory in which files listed in the file manifest
            should be located.
        :type input_path: str
        """
        self.input_path = input_path
        self.dataset_design_class = dataset_design_class
        if not exists(file_manifest_file):
            raise FileNotFoundError(file_manifest_file)
        self.file_metadata = pd.read_csv(file_manifest_file, sep='\t')

    def retrieve_file_records(self, condition=lambda x: True):
        return [
            record
            for i, record in self.file_metadata.iterrows()
            if condition(record)
        ]

    def write_job_specification_table(self, job_specification_table_filename, outcomes_file):
        """
        Prepares the job specification table for the orchestrator.
        """
        outcomes = pd.read_csv(outcomes_file, sep='\t')
        outcomes_dict = {
            row['Sample ID'] : row[outcomes.columns[1]]
            for i, row in outcomes.iterrows()
        }

        validate = self.dataset_design_class.validate_cell_manifest_descriptor
        records = self.retrieve_file_records(condition = lambda record: validate(record['Data type']))
        rows = [
            {
                'input_file_identifier' : record['File ID'],
                'input_filename' : join(self.input_path, record['File name']),
                'job_index' : i,
                'sample_identifier' : record['Sample ID'],
                'outcome' : outcomes_dict[record['Sample ID']],
            }
            for i, record in enumerate(records)
        ]
        df = pd.DataFrame(rows)
        columns = df.columns
        df = df[sorted(columns)]
        df.to_csv(job_specification_table_filename, index=False, header=True)

    def write_dataset_metadata_files_list(self, dataset_metadata_files_list_file):
        """
        Prepares the list of additional job input files. Just includes every file in
        the file manifest which is not determined to be a cell manifest.
        """
        validate = self.dataset_design_class.validate_cell_manifest_descriptor
        records = self.retrieve_file_records(condition = lambda record: not validate(record['Data type']))
        filenames = [join(self.input_path, record['File name']) for record in records]
        with open(dataset_metadata_files_list_file, 'wt') as file:
            file.write('\n'.join(filenames))

    def write_filename(self, filename_file, identifier):
        validate = lambda record: record['File ID'] == identifier
        records = self.retrieve_file_records(condition = validate)
        if len(records) != 1:
            raise ValueError('Found %s files "%s"; need exactly 1.' % (str(len(records)), identifier))
        with open(filename_file, 'wt') as file:
            file.write(join(self.input_path, records[0]['File name']))

    def write_elementary_phenotypes_filename(self, filename_file):
        self.write_filename(filename_file, elementary_phenotypes_file_identifier)

    def write_composite_phenotypes_filename(self, filename_file):
        self.write_filename(filename_file, composite_phenotypes_file_identifier)

    def write_outcomes_filename(self, filename_file):
        validate = lambda record: record['Data type'] == 'Outcome'
        records = self.retrieve_file_records(condition = validate)
        if len(records) != 1:
            raise ValueError('Found %s files "%s"; *currently* need exactly 1.' % (str(len(records)), identifier))
        with open(filename_file, 'wt') as file:
            file.write(join(self.input_path, records[0]['File name']))

    # project_handle = sorted(list(set(self.file_metadata['Project ID']).difference([''])))[0]
    # if project_handle != '':
    #     logger.info('Dataset/project: %s', project_handle)
    #     current = datetime.datetime.now()
    #     year = current.date().strftime("%Y")
    #     logger.info('Run date year: %s', year)
