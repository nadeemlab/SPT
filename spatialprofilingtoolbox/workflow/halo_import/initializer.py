"""The initializer of the main data import workflow."""
from abc import ABC, abstractmethod

from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.workflow.source_file_adi_parsing.skimmer import DataSkimmer
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class Initializer(ABC):
    """Interface for the intializer job for the Nextflow-managed workflows."""
    def __init__(self, dataset_design=None, computational_design=None, **kwargs): # pylint: disable=unused-argument
        self.dataset_design = dataset_design
        self.computational_design = computational_design

    @staticmethod
    @abstractmethod
    def solicit_cli_arguments(parser):
        pass

    @abstractmethod
    def initialize(self, **kwargs):
        pass


class HALOImportInitializer(Initializer):
    """Initial process for main data import workflow; does most of the import."""

    @staticmethod
    def solicit_cli_arguments(parser):
        add_argument(parser, 'file manifest')
        add_argument(parser, 'study file')
        add_argument(parser, 'database config')
        add_argument(parser, 'channels file')
        add_argument(parser, 'phenotypes file')
        add_argument(parser, 'outcomes file')
        add_argument(parser, 'subjects file')
        add_argument(parser, 'diagnosis file')
        add_argument(parser, 'interventions file')

    def initialize(self, database_config_file: str = '', **kwargs):
        if database_config_file == '':
            message = 'Need to supply database configuration file.'
            logger.error(message)
            raise ValueError(message)
        with DataSkimmer(database_config_file=database_config_file) as skimmer:
            skimmer.parse(
                {
                    'file manifest': kwargs['file_manifest_file'],
                    'channels': kwargs['elementary_phenotypes_file'],
                    'phenotypes': kwargs['composite_phenotypes_file'],
                    'samples': kwargs['outcomes_file'],
                    'subjects': kwargs['subjects_file'],
                    'study': kwargs['study_file'],
                    'diagnosis': kwargs['diagnosis_file'],
                    'interventions': kwargs['interventions_file'],
                },
                dataset_design=self.dataset_design,
                computational_design=self.computational_design,
            )
