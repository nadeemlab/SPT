import importlib.resources
import urllib.request
from urllib.request import urlopen
import os
from os.path import exists
from os.path import join
from os.path import expanduser
from os import remove
import sqlite3
import configparser

import psycopg2
import pandas as pd

from .log_formats import colorized_logger
logger = colorized_logger(__name__)

from .source_file_parsers import *


class DataSkimmer:
    pathstudies_db_filename = 'normalized_source_data.db'

    def __init__(self, dataset_design, input_path, file_manifest_file, skip_semantic_parse=None, db_backend=DBBackend.POSTGRES):
        connectivity = False
        self.db_backend = None
        self.input_path = input_path
        self.file_manifest_file = file_manifest_file

        if skip_semantic_parse:
            logger.info('Skipping semantic parse.')
            return

        if db_backend == DBBackend.SQLITE:
            self.db_backend = DBBackend.SQLITE

        if db_backend != DBBackend.SQLITE:
            connectivity = self.check_internet_connectivity()
            if not connectivity:
                logger.info('No internet connection.')

            configured_credentials = self.retrieve_credentials()
            found = [key in configured_credentials for key in self.get_credential_keys()]
            if all(found):
                credentials = {c : configured_credentials[c] for c in self.get_credential_keys()}
                logger.info('Found database credentials %s', self.get_credential_keys())
                if (not connectivity) and (credentials['endpoint'] != 'localhost'):
                    message = 'Without network connection, you can only use endpoint=localhost for backend database.'
                    logger.error(message)
                    raise ConnectionError(message)
                self.db_backend = DBBackend.POSTGRES
            elif not any(found):
                logger.info('No database credentials found.')
                self.db_backend = DBBackend.SQLITE
            else:
                logger.error(
                    'Some database credentials missing: %s',
                    [c for c in self.get_credential_keys() if not c in configured_credentials]
                )
                raise EnvironmentError

        self.connection = None
        if self.db_backend == DBBackend.POSTGRES:
            try:
                self.connection = psycopg2.connect(
                    dbname='pathstudies',
                    host=credentials['endpoint'],
                    user=credentials['user'],
                    password=credentials['password'],
                )
            except psycopg2.Error as e:
                print(e)
                logger.error('Failed to connect to database: %s', e.pgerror)
                logger.debug('Trying sqlite locally instead.')
                self.db_backend = DBBackend.SQLITE

        if self.db_backend == DBBackend.SQLITE:
            logger.info('Using sqlite backend.')
            with importlib.resources.path('spatialprofilingtoolbox', 'pathology_schema.sql') as path:
                create_db_script = open(path).read()
            pathstudies = DataSkimmer.pathstudies_db_filename
            if exists(pathstudies):
                remove(pathstudies)
            self.connection = sqlite3.connect(pathstudies)
            logger.info('sqlite backend: %s', pathstudies)
            cursor = self.connection.cursor()
            cursor.executescript(create_db_script)
            cursor.close()

        if not self.db_backend in [DBBackend.POSTGRES, DBBackend.SQLITE]:
            message = 'Still no database connection established. Maybe you want to use skip_semantic_parse=True .'
            logger.error(message)
            raise ConnectionError(message)

        self.dataset_design = dataset_design

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.connection:
            self.connection.close()

    def get_credential_keys(self):
        return ['endpoint', 'user', 'password']

    def retrieve_credentials(self):
        config_file = join(expanduser('~'), '.spt_db.config')
        parser = configparser.ConfigParser()
        credentials = {}
        if exists(config_file):
            parser.read(config_file)
            if 'database-credentials' in parser.sections():
                for key in self.get_credential_keys():
                    if key in parser['database-credentials']:
                        credentials[key] = parser['database-credentials'][key]
        else:
            logger.info('Config file %s not found.', config_file)
        return credentials

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
            with open(DataSkimmer.pathstudies_db_filename, 'w') as f:
                f.write('')
            return
        with importlib.resources.path('spatialprofilingtoolbox', 'fields.tsv') as path:
            fields = pd.read_csv(path, sep='\t', na_filter=False)

        args = [self.connection, fields, self.dataset_design]
        kwargs = {
            'db_backend' : self.db_backend,
            'input_path' : self.input_path,
            'file_manifest_file' : self.file_manifest_file,
        }
        OutcomesParser(**kwargs).parse(*args)
        CellManifestSetParser(**kwargs).parse(*args)
        chemical_species_identifiers_by_symbol = ChannelsPhenotypesParser(**kwargs).parse(*args)
        CellManifestsParser(chemical_species_identifiers_by_symbol, **kwargs).parse(*args)

    def skim_final_data(self):
        pass
        # two cohort feature assocation test
        # feature specification
        # feaure specifier
        # diagnostic selection criterion
