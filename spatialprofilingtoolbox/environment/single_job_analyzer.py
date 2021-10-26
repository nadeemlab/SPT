import functools
from functools import lru_cache
import hashlib

import pandas as pd

from .database_context_utility import WaitingDatabaseContextManager
from .settings_wrappers import DatasetSettings
from .file_io import get_input_filename_by_identifier
from .log_formats import colorized_logger

logger = colorized_logger(__name__)


class SingleJobAnalyzer:
    """
    An interface for a single job to be executed as part of a batch in a pipeline
    run. It handles some "boilerplate".
    """
    def __init__(self,
        input_path: str=None,
        file_manifest_file: str=None,
        input_file_identifier: str=None,
        dataset_design=None,
        computational_design=None,
        **kwargs,
    ):
        """
        Args:
            input_path (str):
                The directory in which files listed in the file manifest should be
                located.
            file_manifest_file (str):
                The file manifest file, in the format of the specification distributed
                with the source code of this package.
            outcomes_file (str):
                A tabular text file assigning outcome values (in second column) to
                sample identifiers (first column).
            input_file_identifier (str):
                The identifier, as it appears in the file manifest, for the file
                associated with this job.
        """
        self.dataset_settings = DatasetSettings(
            input_path,
            file_manifest_file,
        )
        self.input_file_identifier = input_file_identifier
        self.dataset_design = dataset_design
        self.computational_design = computational_design

    def _calculate(self):
        """
        Abstract method, the implementation of which is the core/primary computation to
        be performed by this job.
        """
        pass

    def calculate(self):
        """
        The main calculation of this job, to be called by pipeline orchestration.
        """
        self.initialize_intermediate_database()
        self._calculate()

    def retrieve_input_filename(self):
        self.get_input_filename()

    def retrieve_sample_identifier(self):
        self.get_sample_identifier()

    @lru_cache(maxsize=1)
    def get_input_filename(self):
        """
        See ``get_input_filename_by_identifier``. Applied to this job's specific
        ``input_file_identifier``.
        """
        return get_input_filename_by_identifier(
            dataset_settings = self.dataset_settings,
            file_metadata = pd.read_csv(self.dataset_settings.file_manifest_file, sep='\t'),
            input_file_identifier = self.input_file_identifier,
        )

    @lru_cache(maxsize=1)
    def get_sample_identifier(self):
        """
        Uses the file identifier to lookup and cache the associated sample identifier.
        """
        file_metadata = pd.read_csv(self.dataset_settings.file_manifest_file, sep='\t')
        records = file_metadata[file_metadata['File ID'] == self.input_file_identifier]
        for i, row in records.iterrows():
            sample_identifier = row['Sample ID']
            return sample_identifier

    def initialize_intermediate_database(self):
        pass
