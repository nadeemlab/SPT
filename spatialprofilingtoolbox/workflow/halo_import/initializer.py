"""The initializer of the main data import workflow."""
from typing import Optional

from spatialprofilingtoolbox.workflow.defaults.cli_arguments import add_argument
from spatialprofilingtoolbox.workflow.defaults.initializer import Initializer
from spatialprofilingtoolbox.workflow.source_file_adi_parsing.skimmer import DataSkimmer
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class HALOImportInitializer(Initializer):
    """Initial process for main data import workflow; does most of the import."""
    def __init__(self,
                 file_manifest_file=None,
                 elementary_phenotypes_file=None,
                 composite_phenotypes_file=None,
                 outcomes_file=None,
                 compartments_file=None,
                 subjects_file=None,
                 **kwargs,
                 ):
        super().__init__(**kwargs)
        self.file_manifest_file = file_manifest_file
        self.elementary_phenotypes_file = elementary_phenotypes_file
        self.composite_phenotypes_file = composite_phenotypes_file
        self.outcomes_file = outcomes_file
        self.compartments_file = compartments_file
        self.subjects_file = subjects_file

    @staticmethod
    def solicit_cli_arguments(parser):
        add_argument(parser, 'file manifest')
        add_argument(parser, 'study file')
        add_argument(parser, 'database config')
        add_argument(parser, 'channels file')
        add_argument(parser, 'phenotypes file')
        add_argument(parser, 'outcomes file')
        add_argument(parser, 'compartments file')
        add_argument(parser, 'subjects file')
        add_argument(parser, 'diagnosis file')
        add_argument(parser, 'interventions file')

    def initialize(
        self,
        database_config_file: Optional[str] = None,
        **kwargs,
    ):
        if database_config_file is None:
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
                    'compartments': kwargs['compartments_file'],
                    'subjects': kwargs['subjects_file'],
                    'study': kwargs['study_file'],
                    'diagnosis': kwargs['diagnosis_file'],
                    'interventions': kwargs['interventions_file'],
                },
                dataset_design=self.dataset_design,
                computational_design=self.computational_design,
            )
