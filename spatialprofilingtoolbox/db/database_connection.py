"""
A context manager from accessing the backend SPT database, from inside library
functions.
"""
from os.path import exists
from os.path import abspath
from os.path import expanduser
from typing import Optional
from urllib.error import URLError
from urllib.request import urlopen
import re
import configparser

from psycopg2 import connect
from psycopg2.extensions import connection as Psycopg2Connection
from psycopg2 import Error as Psycopg2Error

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def retrieve_credentials(database_config_file):
    parser = configparser.ConfigParser()
    credentials = {}
    parser.read(database_config_file)
    if 'database-credentials' in parser.sections():
        for key in get_credential_keys():
            if key in parser['database-credentials']:
                credentials[key] = parser['database-credentials'][key]
    if not re.match('^[a-z][a-z0-9_]+[a-z0-9]$', credentials['database']):
        logger.warning(
            'The database name "%s" is too complex. Reverting to "postgres".',
            credentials['database'])
        credentials['database'] = 'postgres'
    return credentials


def get_credential_keys():
    return ['endpoint', 'database', 'user', 'password']


def check_internet_connectivity():
    try:
        test_host = 'https://duckduckgo.com'
        with urlopen(test_host) as _:
            return True
    except URLError:
        return False


def check_credentials_availability(configured_credentials):
    connectivity = check_internet_connectivity()
    if not connectivity:
        logger.info('No internet connection.')

    found = [key in configured_credentials for key in get_credential_keys()]
    if all(found):
        credentials = {c: configured_credentials[c]
                       for c in get_credential_keys()}
        if (not connectivity) and (credentials['endpoint'] in ['localhost', '127.0.0.1']):
            message = 'Without network connection, you can only use endpoint=localhost for ' \
                'backend database.'
            logger.error(message)
            raise ConnectionError(message)
    else:
        logger.error(
            'Some database credentials missing: %s',
            [c for c in get_credential_keys() if not c in configured_credentials]
        )
        raise EnvironmentError


class DatabaseConnectionMaker:
    """
    Provides a psycopg2 Postgres database connection. Takes care of connecting
    and disconnecting.
    """
    connection: Psycopg2Connection

    def __init__(self, database_config_file: Optional[str] = None):
        credentials = retrieve_credentials(database_config_file)
        check_credentials_availability(credentials)
        try:
            self.connection = connect(
                dbname=credentials['database'],
                host=credentials['endpoint'],
                user=credentials['user'],
                password=credentials['password'],
            )
        except Psycopg2Error as excepted:
            logger.error('Failed to connect to database: %s %s',
                         credentials['endpoint'], credentials['database'])
            raise excepted

    def is_connected(self):
        try:
            connection = self.connection
            return connection is not None
        except AttributeError:
            return False

    def get_connection(self):
        return self.connection

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.connection:
            self.connection.close()

def get_and_validate_database_config(args):
    if args.database_config_file:
        config_file = abspath(expanduser(args.database_config_file))
        if not exists(config_file):
            raise FileNotFoundError(
                f'Need to supply valid database config filename: {config_file}')
        return config_file
    raise ValueError('Could not parse CLI argument for database config.')
