import importlib.resources

import psycopg2
import pandas as pd

from .log_formats import colorized_logger
logger = colorized_logger(__name__)

from .source_file_parsers import *


class DataSkimmer:
    def __init__(self, endpoint, user, password, dataset_settings, dataset_design):
        try:
            self.connection = psycopg2.connect(
                dbname='pathstudies',
                user=user,
                password=password,
                host=endpoint,
            )
        except psycopg2.Error as e:
            logger.error('Failed to connect to database: %s', e.pgerror)
        self.dataset_settings = dataset_settings
        self.dataset_design = dataset_design

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.connection.close()

    def skim_initial_data(self):
        with importlib.resources.path('spatialprofilingtoolbox', 'fields.tsv') as path:
            fields = pd.read_csv(path, sep='\t', na_filter=False)

        args = [self.connection, fields, self.dataset_settings, self.dataset_design]
        OutcomesParser().parse(*args)
        CellManifestSetParser().parse(*args)
        chemical_species_identifiers_by_symbol = ChannelsPhenotypesParser().parse(*args)
        CellManifestsParser(chemical_species_identifiers_by_symbol).parse(*args)

    def skim_final_data(self):
        pass
        # two cohort feature assocation test
        # feature specification
        # feaure specifier
        # diagnostic selection criterion
