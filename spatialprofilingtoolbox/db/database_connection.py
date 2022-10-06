import urllib.request
from urllib.request import urlopen
import re
import configparser

import psycopg2

from ..standalone_utilities.log_formats import colorized_logger
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
        logger.warning('The database name "%s" is too complex. Reverting to "postgres".', credentials['database'])
        credentials['database'] = 'postgres'
    return credentials


def get_credential_keys():
    return ['endpoint', 'database', 'user', 'password']


def check_internet_connectivity():
    try:
        test_host = 'https://duckduckgo.com'
        urlopen(test_host)
        return True
    except:
        return False


def check_credentials_availability(configured_credentials):
    connectivity = check_internet_connectivity()
    if not connectivity:
        logger.info('No internet connection.')

    found = [key in configured_credentials for key in get_credential_keys()]
    if all(found):
        credentials = {c : configured_credentials[c] for c in get_credential_keys()}
        logger.info('Found database credentials %s', get_credential_keys())
        logger.info('endpoint: %s', credentials['endpoint'])
        logger.info('database: %s', credentials['database'])
        logger.info('user:     %s', credentials['user'])
        if (not connectivity) and (credentials['endpoint'] in ['localhost', '127.0.0.1']):
            message = 'Without network connection, you can only use endpoint=localhost for backend database.'
            logger.error(message)
            raise ConnectionError(message)
    else:
        logger.error(
            'Some database credentials missing: %s',
            [c for c in get_credential_keys() if not c in configured_credentials]
        )
        raise EnvironmentError


class DatabaseConnectionMaker:
    def __init__(self, database_config_file: str=None):
        credentials = retrieve_credentials(database_config_file)
        check_credentials_availability(credentials)
        self.connection = None
        try:
            self.connection = psycopg2.connect(
                dbname=credentials['database'],
                host=credentials['endpoint'],
                user=credentials['user'],
                password=credentials['password'],
            )
        except psycopg2.Error as e:
            logger.error('Failed to connect to database: %s %s', credentials['endpoint'], credentials['database'])
            raise e

    def get_connection(self):
        return self.connection

