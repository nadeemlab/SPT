import os
from os.path import join, exists, isfile
import datetime

import pandas as pd

from .configuration_settings import file_manifest_filename
from .extract_compartments import extract_compartments
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
        dataset_design_class=None,
        input_path: str=None,
        job_inputs: str=None,
        all_jobs_inputs: str=None,
        compartments_file: str=None,
        **kwargs,
    ):
        """
        :param dataset_design_class: Class of design object representing input data set.

        :param input_path: The directory in which files listed in the file manifest
            should be located.
        :type input_path: str

        :param job_inputs: Output file to which to write list of additional inputs.
        :type job_inputs: str
        """
        self.dataset_design_class = dataset_design_class
        self.input_path = input_path
        self.job_inputs = job_inputs
        self.all_jobs_inputs = all_jobs_inputs
        self.compartments_file = compartments_file
        self.file_metadata = pd.read_csv(file_manifest_filename, sep='\t')

    def print_job_specification_table(self):
        """
        Prepares the job specification table for the orchestrator.
        """
        attributes = ['input_file_identifier']

        rows = []
        job_count = 0
        for i, file_row in self.file_metadata.iterrows():
            descriptor = file_row['Data type']
            validated = self.dataset_design_class.validate_cell_manifest_descriptor(descriptor)
            if validated:
                input_file_identifier = file_row['File ID']
                input_filename = file_row['File name']
                full_filename = join(self.input_path, input_filename)
                job_index = job_count
                job_count += 1
                rows.append({
                    'input_file_identifier' : input_file_identifier,
                    'input_filename' : full_filename,
                    'job_index' : job_index,
                })
        df = pd.DataFrame(rows)
        columns = df.columns
        df = df[sorted(columns)]
        table_str = df.to_csv(index=False, header=True)

        print(table_str)

    def list_auxiliary_job_inputs(self):
        """
        Prepares the list of additional job input files. Just includes every file in
        the file manifest which is not determined to be a cell manifest.
        """
        filenames = []
        for i, file_row in self.file_metadata.iterrows():
            descriptor = file_row['Data type']
            validated = self.dataset_design_class.validate_cell_manifest_descriptor(descriptor)
            if (not validated) or (not self.job_specification_by_file()):
                input_filename = file_row['File name']
                full_filename = join(self.input_path, input_filename)
                filenames.append(full_filename)
        df = pd.DataFrame({'filename' : filenames})
        df.to_csv(self.job_inputs, index=False, header=False)
        project_handle = sorted(list(set(self.file_metadata['Project ID']).difference([''])))[0]
        if project_handle != '':
            logger.info('Dataset/project: %s', project_handle)
            current = datetime.datetime.now()
            year = current.date().strftime("%Y")
            logger.info('Run date year: %s', year)

    def list_all_jobs_inputs(self):
        """
        Prepares the list of additional job input files. Just includes every file in
        the file manifest which is not determined to be a cell manifest.
        """
        filenames = []
        for i, file_row in self.file_metadata.iterrows():
            input_filename = file_row['File name']
            full_filename = join(self.input_path, input_filename)
            filenames.append(full_filename)
        df = pd.DataFrame({'filename' : filenames})
        print(self.all_jobs_inputs)
        df.to_csv(self.all_jobs_inputs, index=False, header=False)

    def list_all_compartments(self):
        compartments = extract_compartments(
            self.dataset_design_class.get_cell_manifest_descriptor(),
        )
        df = pd.DataFrame({'compartment' : compartments})
        print(compartments)
        df.to_csv(self.compartments_file, index=False, header=False)
