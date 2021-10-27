import os
from os.path import join, exists, isfile

import pandas as pd

from .settings_wrappers import DatasetSettings
from .log_formats import colorized_logger

logger = colorized_logger(__name__)


class JobGenerator:
    """
    An interface for pipeline job generation. Minimally assumes that the pipeline
    acts on input files listed in a file manifest file, itself in a format
    controlled by a relatively precise schema (distributed with the source code of
    this package).

    The schema has 11 fields for each file and includes hashes.
    """
    def __init__(self,
        input_path: str=None,
        file_manifest_file: str=None,
        job_inputs: str=None,
        dataset_design_class=None,
        **kwargs,
    ):
        """
        :param input_path: The directory in which files listed in the file manifest
            should be located.
        :type input_path: str

        :param file_manifest_file: The file manifest file, in the format of the
            specification distributed with the source code of this package.
        :type file_manifest_file: str

        :param job_inputs: Output file to which to write list of additional inputs.
        :type job_inputs: str

        :param dataset_design_class: Class of design object representing input data set.
        """
        self.job_inputs = job_inputs
        self.dataset_settings = DatasetSettings(
            input_path,
            file_manifest_file,
        )

        self.file_metadata = pd.read_csv(self.dataset_settings.file_manifest_file, sep='\t')
        self.dataset_design_class = dataset_design_class

    def generate(self):
        """
        This is the main exposed API call. Should generate the job specification table.
        """
        self.generate_job_specification_table()

    def generate_job_specification_table(self):
        """
        Prepares the job specification table for the nextflow script.
        """
        attributes = ['input_file_identifier'] if self.job_specification_by_file() else []

        if not self.job_specification_by_file():
            df = pd.DataFrame([{
                'input_file_identifier': 'all files',
                'input_filename': 'all filenames',
                'job_index' : 0,
            }])
            table_str = df.to_csv(index=False, header=True)
        
        if self.job_specification_by_file():
            rows = []
            job_count = 0
            for i, file_row in self.file_metadata.iterrows():
                descriptor = file_row['Data type']
                validated = self.dataset_design_class.validate_cell_manifest_descriptor(descriptor)
                if validated:
                    input_file_identifier = file_row['File ID']
                    input_filename = file_row['File name']
                    full_filename = join(self.dataset_settings.input_path, input_filename)
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
                full_filename = join(self.dataset_settings.input_path, input_filename)
                filenames.append(full_filename)
        df = pd.DataFrame({'filename' : filenames})
        df.to_csv(self.job_inputs, index=False, header=False)

    @staticmethod
    def get_memory_requirements(file_record):
        """
        :param file_record: Record as it would appear in the file metadata table.
        :type file_record: dict

        :return: ``memory_in_gb``. The positive integer number of gigabytes to request
            for a job involving the given input file.
        :rtype: int

        * May be deprecated in the future.
        """
        file_size_gb = float(file_record['Size']) / pow(10, 9)
        return 1 + math.ceil(file_size_gb * 10)

    def job_specification_by_file(self):
        pass

