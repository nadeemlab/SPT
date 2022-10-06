
from ..defaults.initializer import Initializer
from ...source_file_adi_parsing.skimmer import DataSkimmer
from ....standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class HALOImportInitializer(Initializer):
    def __init__(self,
            file_manifest_file = None,
            elementary_phenotypes_file = None,
            composite_phenotypes_file = None,
            outcomes_file = None,
            compartments_file = None,
            subjects_file = None,
            **kwargs,
        ):
        super(HALOImportInitializer, self).__init__(**kwargs)
        self.file_manifest_file = file_manifest_file
        self.elementary_phenotypes_file = elementary_phenotypes_file
        self.composite_phenotypes_file = composite_phenotypes_file
        self.outcomes_file = outcomes_file
        self.compartments_file = compartments_file
        self.subjects_file = subjects_file

    @staticmethod
    def solicit_cli_arguments(parser):
        parser.add_argument(
            '--file-manifest-file',
            dest='file_manifest_file',
            type=str,
            required=False,
        )
        parser.add_argument(
            '--database-config-file',
            dest='database_config_file',
            type=str,
            required=False,
        )
        parser.add_argument(
            '--elementary-phenotypes-file',
            dest='elementary_phenotypes_file',
            type=str,
            required=False,
        )
        parser.add_argument(
            '--composite-phenotypes-file',
            dest='composite_phenotypes_file',
            type=str,
            required=False,
        )
        parser.add_argument(
            '--outcomes-file',
            dest='outcomes_file',
            type=str,
            required=False,
            help='The outcome assignments file.'
        )
        parser.add_argument(
            '--compartments-file',
            dest='compartments_file',
            type=str,
            required=False,
            help='File containing compartment names.'
        )
        parser.add_argument(
            '--subjects-file',
            dest='subjects_file',
            type=str,
            required=False,
            help='File containing subject information: age at specimen collection, sex, diagnosis.'
        )

    def initialize(
        self,
        database_config_file: str=None,
        **kwargs,
    ):
        if database_config_file is None:
            message = 'Need to supply database configuration file.'
            logger.error(message)
            raise ValueError(message)
        with DataSkimmer(database_config_file=database_config_file) as skimmer:
            skimmer.parse(
                dataset_design=self.dataset_design,
                computational_design=self.computational_design,
                **kwargs,
            )
