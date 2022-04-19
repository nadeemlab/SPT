import importlib.resources
import urllib.request
from urllib.request import urlopen
import os
from os.path import exists
from os import remove
import sqlite3

import psycopg2
import pandas as pd

from .log_formats import colorized_logger
logger = colorized_logger(__name__)

from .source_file_parsers import *


class DataSkimmer:
    def __init__(self, dataset_settings, dataset_design, skip_semantic_parse=None):
        connectivity = False
        self.db_backend = None

        skip = False
        if not skip_semantic_parse is None:
            if skip_semantic_parse in [True, 'true', 'True', '1', 1]:
                skip = True
                logger.info('Skipping semantic parse unless database credentials are provided.')

        connectivity = self.check_internet_connectivity()
        if not connectivity:
            logger.info('No internet connection.')
            if not skip:
                logger.info('Using sqlite backend.')
                self.db_backend = DBBackend.SQLITE

        if connectivity:
            credential_parameters = [
                'PATHSTUDIES_DB_ENDPOINT',
                'PATHSTUDIES_DB_USER',
                'PATHSTUDIES_DB_PASSWORD',
            ]
            found = [key in os.environ for key in credential_parameters]
            if all(found):
                credentials = {c : os.environ[c] for c in credential_parameters}
                logger.info('Found database credentials %s', credential_parameters)
                self.db_backend = DBBackend.POSTGRES
            if not any(found):
                logger.info('No database credentials found.')
                if not skip:
                    logger.info('Using sqlite backend.')
                    self.db_backend = DBBackend.SQLITE
            else:
                if not all(found):
                    logger.error(
                        'Some database credentials missing: %s',
                        [c for c in credential_parameters if not c in os.environ]
                    )
                    raise EnvironmentError

        self.connection = None
        if self.db_backend == DBBackend.POSTGRES:
            try:
                self.connection = psycopg2.connect(
                    dbname='pathstudies',
                    host=credentials['PATHSTUDIES_DB_ENDPOINT'],
                    user=credentials['PATHSTUDIES_DB_USER'],
                    password=credentials['PATHSTUDIES_DB_PASSWORD'],
                )
            except psycopg2.Error as e:
                logger.error('Failed to connect to database: %s', e.pgerror)
                logger.debug('Trying sqlite locally instead.')
                self.db_backend = DBBackend.SQLITE

        if self.db_backend == DBBackend.SQLITE:
            with importlib.resources.path('spatialprofilingtoolbox', 'pathology_schema.sql') as path:
                create_db_script = open(path).read()
            pathstudies = 'normalized_source_data.db'
            if exists(pathstudies):
                remove(pathstudies)
            self.connection = sqlite3.connect(pathstudies)
            logger.info('sqlite backend: %s', pathstudies)
            cursor = self.connection.cursor()
            cursor.executescript(create_db_script)
            cursor.close()

        self.dataset_settings = dataset_settings
        self.dataset_design = dataset_design

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.connection:
            self.connection.close()

    def check_internet_connectivity(self):
        try:
            test_host = 'https://duckduckgo.com'
            urlopen(test_host)
            return True
        except:
            return False

    def parse(self):
        if not self.connection:
            logger.debug('No database connection was initialized. Skipping semantic parse.')
            with open('normalized_source_data.db', 'w') as f:
                f.write('')
            return
        with importlib.resources.path('spatialprofilingtoolbox', 'fields.tsv') as path:
            fields = pd.read_csv(path, sep='\t', na_filter=False)

        args = [self.connection, fields, self.dataset_settings, self.dataset_design]
        OutcomesParser(db_backend=self.db_backend).parse(*args)
        CellManifestSetParser(db_backend=self.db_backend).parse(*args)
        chemical_species_identifiers_by_symbol = ChannelsPhenotypesParser(db_backend=self.db_backend).parse(*args)
        CellManifestsParser(chemical_species_identifiers_by_symbol, db_backend=self.db_backend).parse(*args)

    def skim_final_data(self):
        pass
        # two cohort feature assocation test
        # feature specification
        # feaure specifier
        # diagnostic selection criterion
