"""
Generate the list of jobs for tabular import.
"""
from os.path import join
from os.path import exists
from typing import Optional

import pandas as pd

from spatialprofilingtoolbox.workflow.component_interfaces.job_generator import JobGenerator
from spatialprofilingtoolbox.workflow.tabular_import.tabular_dataset_design\
    import TabularCellMetadataDesign
from spatialprofilingtoolbox.workflow.common.file_identifier_schema \
    import ELEMENTARY_PHENOTYPES_FILE_IDENTIFIER
from spatialprofilingtoolbox.workflow.common.file_identifier_schema \
    import COMPOSITE_PHENOTYPES_FILE_IDENTIFIER
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class TabularImportJobGenerator(JobGenerator):
    """
    Generate the list of jobs for tabular import.
    """

    def __init__(self,
                 input_path: Optional[str] = None,
                 file_manifest_file: Optional[str] = None,
                 dataset_design_class=TabularCellMetadataDesign
                 ):
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

    def write_job_specification_table(self, job_specification_table_filename, outcomes_file=None):
        """
        Prepares the job specification table for the orchestrator.
        """
        validate = self.dataset_design_class.validate_cell_manifest_descriptor
        records = self.retrieve_file_records(
            condition=lambda record: validate(record['Data type']))

        if outcomes_file:
            outcomes = pd.read_csv(outcomes_file, sep='\t')
            outcomes_dict = {
                row['Sample ID']: row[outcomes.columns[1]]
                for i, row in outcomes.iterrows()
            }
        else:
            outcomes_dict = {
                record['Sample ID']: 'Unknown outcome assignment'
                for i, record in enumerate(records)
            }

        rows = [
            {
                'input_file_identifier': record['File ID'],
                'input_filename': join(self.input_path, record['File name']),
                'job_index': i,
                'outcome': outcomes_dict[record['Sample ID']],
                'sample_identifier': record['Sample ID'],
            }
            for i, record in enumerate(records)
        ]
        df = pd.DataFrame(rows)
        columns = df.columns
        df = df[sorted(columns)]
        df.to_csv(job_specification_table_filename, index=False, header=True)

    def write_filename(self, filename_file, identifier):
        def validate(record):
            return record['File ID'] == identifier
        records = self.retrieve_file_records(condition=validate)
        if len(records) != 1:
            raise ValueError(
                f'Found {len(records)} files "{identifier}"; need exactly 1.')
        with open(filename_file, 'wt', encoding='utf-8') as file:
            file.write(join(self.input_path, records[0]['File name']))

    def write_elementary_phenotypes_filename(self, filename_file):
        self.write_filename(
            filename_file, ELEMENTARY_PHENOTYPES_FILE_IDENTIFIER)

    def write_composite_phenotypes_filename(self, filename_file):
        self.write_filename(
            filename_file, COMPOSITE_PHENOTYPES_FILE_IDENTIFIER)