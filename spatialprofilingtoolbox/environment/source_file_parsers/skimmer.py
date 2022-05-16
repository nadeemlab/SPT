import importlib.resources
import urllib.request
from urllib.request import urlopen
import re
import configparser

import psycopg2
import pandas as pd

from ..logging.log_formats import colorized_logger
logger = colorized_logger(__name__)

from .outcomes import OutcomesParser
from .cellmanifestset import CellManifestSetParser
from .channels import ChannelsPhenotypesParser
from .cellmanifests import CellManifestsParser
from .parser import DBBackend


class DataSkimmer:
    def __init__(self, database_config_file: str=None, db_backend=DBBackend.POSTGRES):
        self.config_file = config_file
        if db_backend == DBBackend.POSTGRES:
            self.check_credentials_availability()
            self.db_backend = db_backend
        else:
            raise ValueError('Only DBBackend.POSTGRES is supported.')
        self.connection = None
        try:
            credentials = self.retrieve_credentials()
            self.connection = psycopg2.connect(
                dbname=credentials['database'],
                host=credentials['endpoint'],
                user=credentials['user'],
                password=credentials['password'],
            )
        except psycopg2.Error as e:
            logger.error('Failed to connect to database: %s %s', credentials['endpoint'], credentials['database'])
            raise e

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.connection:
            self.connection.close()

    def check_credentials_availability(self):
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
        else:
            logger.error(
                'Some database credentials missing: %s',
                [c for c in self.get_credential_keys() if not c in configured_credentials]
            )
            raise EnvironmentError

    def check_internet_connectivity(self):
        try:
            test_host = 'https://duckduckgo.com'
            urlopen(test_host)
            return True
        except:
            return False

    def get_credential_keys(self):
        return ['endpoint', 'database', 'user', 'password']

    def retrieve_credentials(self):
        parser = configparser.ConfigParser()
        credentials = {}
        parser.read(self.config_file)
        if 'database-credentials' in parser.sections():
            for key in self.get_credential_keys():
                if key in parser['database-credentials']:
                    credentials[key] = parser['database-credentials'][key]
        if not re.match('^[a-z][a-z0-9_]+[a-z0-9]$', credentials['database']):
            logger.warning('The database name "%s" is too complex. Reverting to "postgres".', credentials['database'])
            credentials['database'] = 'postgres'
        return credentials

    def parse(
            self,
            dataset_design = None,
            file_manifest_file = None,
            elementary_phenotypes_file = None,
            composite_phenotypes_file = None,
            outcomes_file = None,
            compartments_file = None,
        ):
        if not self.connection:
            logger.debug('No database connection was initialized. Skipping semantic parse.')
            return
        with importlib.resources.path('spatialprofilingtoolbox.data_model', 'fields.tsv') as path:
            fields = pd.read_csv(path, sep='\t', na_filter=False)

        self.create_tables(self.connection)
        OutcomesParser().parse(
            self.connection,
            fields,
            outcomes_file,
        )
        CellManifestSetParser().parse(
            self.connection,
            fields,
            file_manifest_file,
        )
        chemical_species_identifiers_by_symbol = ChannelsPhenotypesParser().parse(
            self.connection,
            fields,
            file_manifest_file,
            elementary_phenotypes_file,
            composite_phenotypes_file,
        )
        CellManifestsParser().parse(
            self.connection,
            fields,
            file_manifest_file,
            chemical_species_identifiers_by_symbol
        )

    def create_tables(self, connection):
        with importlib.resources.path('spatialprofilingtoolbox.data_model', 'pathology_schema.sql') as path:
            create_db_script = open(path).read()
        cursor = connection.cursor()
        cursor.executescript(create_db_script)
        cursor.close()
