"""
The parallelizable, job-level analysis stage of the cell phenotype frequency
analysis workflow.
"""
from os.path import join, abspath
import hashlib

from ...environment.single_job_analyzer import SingleJobAnalyzer
from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.log_formats import colorized_logger
from .core import FrequencyCalculator
from .computational_design import FrequencyDesign

logger = colorized_logger(__name__)


class FrequencyAnalyzer(SingleJobAnalyzer):
    """
    The main class of the job.
    """
    def __init__(self,
        dataset_design=None,
        complex_phenotypes_file: str=None,
        job_index: int=0,
        skip_integrity_check=False,
        **kwargs,
    ):
        """
        :param dataset_design: The design object describing the input data set.

        :param complex_phenotypes_file: The table of composite phenotypes to be
            considered.
        :type complex_phenotypes_file: str
        """
        super().__init__(job_index=job_index, **kwargs)
        self.dataset_design = dataset_design
        self.computational_design = FrequencyDesign(
            dataset_design = self.dataset_design,
            complex_phenotypes_file = complex_phenotypes_file,
        )
        sample_identifiers_by_file = self.retrieve_cell_input_file_info(skip_integrity_check)
        self.calculator = FrequencyCalculator(
            sample_identifiers_by_file = sample_identifiers_by_file,
            jobs_paths = self.jobs_paths,
            dataset_settings = self.dataset_settings,
            dataset_design = self.dataset_design,
            computational_design = self.computational_design,
        )
        logger.info('Job started.')
        logger.info('Note: The "frequency" workflow operates as a single job.')

    def _calculate(self):
        self.calculator.calculate_frequency()

    def retrieve_cell_input_file_info(self, skip_integrity_check):
        """
        :param skip_integrity_check: Whether to calculate checksums and verify that they
            match what appears in the manifest. This option is provided to speed up
            repeated runs.
        :type skip_integrity_check: bool

        :return: Information about the input files with cell data. A dictionary whose
            keys are absolute file paths, and values are sample identifiers associated
            with the files.
        :rtype: dict
        """
        cmd = 'SELECT File_basename, Sample_ID, SHA256, Data_type FROM file_metadata ;'
        with WaitingDatabaseContextManager(self.get_pipeline_database_uri()) as manager:
            result = manager.execute_commit(cmd)

        if skip_integrity_check:
            logger.info('Skipping file integrity checks.')

        sample_identifiers_by_file = {}
        for row in result:
            if row[3] != self.dataset_design.get_cell_manifest_descriptor():
                continue
            input_file = row[0]
            sample_identifier = row[1]
            expected_sha256 = row[2]
            input_file = abspath(join(self.dataset_settings.input_path, input_file))

            if not skip_integrity_check:
                buffer_size = 65536
                sha = hashlib.sha256()
                with open(input_file, 'rb') as file:
                    while True:
                        data = file.read(buffer_size)
                        if not data:
                            break
                        sha.update(data)
                sha256 = sha.hexdigest()
                if sha256 != expected_sha256:
                    logger.error(
                        'File "%s" has wrong SHA256 hash (%s ; expected %s).',
                        row[0],
                        sha256,
                        expected_sha256,
                    )
            sample_identifiers_by_file[input_file] = sample_identifier
        return sample_identifiers_by_file
