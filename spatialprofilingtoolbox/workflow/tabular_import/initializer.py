"""The initializer of the main data import workflow."""

from spatialprofilingtoolbox.workflow.component_interfaces.initializer import Initializer
from spatialprofilingtoolbox.workflow.tabular_import.parsing.skimmer import DataSkimmer
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class TabularImportInitializer(Initializer): #pylint: disable=too-few-public-methods
    """Initial process for main data import workflow; does most of the import."""
    def __init__(self, **kwargs):
        pass

    def initialize(self, database_config_file: str = '', **kwargs):
        if database_config_file == '':
            message = 'Need to supply database configuration file.'
            logger.error(message)
            raise ValueError(message)
        with DataSkimmer(database_config_file=database_config_file) as skimmer:
            skimmer.parse(
                {
                    'file manifest': kwargs['file_manifest_file'],
                    'channels': kwargs['channels_file'],
                    'phenotypes': kwargs['phenotypes_file'],
                    'samples': kwargs['samples_file'],
                    'subjects': kwargs['subjects_file'],
                    'study': kwargs['study_file'],
                    'diagnosis': kwargs['diagnosis_file'],
                    'interventions': kwargs['interventions_file'],
                },
            )
