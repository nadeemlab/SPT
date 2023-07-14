"""Structures and accessors for database credentials."""
from os import environ
import re
import configparser
from typing import NamedTuple

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

class DBCredentials(NamedTuple):
    """Data structure for database credentials."""
    endpoint: str
    database: str
    user: str
    password: str


def get_credentials_from_environment(database_name: str='scstudies') -> DBCredentials:
    _handle_unavailability()
    return DBCredentials(
        environ['SINGLE_CELL_DATABASE_HOST'],
        database_name,
        environ['SINGLE_CELL_DATABASE_USER'],
        environ['SINGLE_CELL_DATABASE_PASSWORD'],
    )

def retrieve_credentials_from_file(database_config_file) -> DBCredentials:
    parser = configparser.ConfigParser()
    credentials = {}
    parser.read(database_config_file)
    if 'database-credentials' in parser.sections():
        for key in set(_get_credential_keys()).intersection(parser['database-credentials'].keys()):
            credentials[key] = parser['database-credentials'][key]
    missing = set(_get_credential_keys()).difference(credentials.keys())
    if len(missing) > 0:
        raise ValueError(f'Database configuration file is missing keys: {missing}')
    if not re.match('^[a-z][a-z0-9_]+[a-z0-9]$', credentials['database']):
        message = 'The database name "%s" is too complex. Reverting to "postgres".'
        logger.warning(message, credentials['database'])
        credentials['database'] = 'postgres'
    return DBCredentials(*[credentials[k] for k in _get_credential_keys()])

def _handle_unavailability():
    variables = [
        'SINGLE_CELL_DATABASE_HOST',
        'SINGLE_CELL_DATABASE_USER',
        'SINGLE_CELL_DATABASE_PASSWORD',
    ]
    unfound = [v for v in variables if not v in environ]
    if len(unfound) > 0:
        raise EnvironmentError(f'Did not find in environment: {str(unfound)}')

def _get_credential_keys():
    return ['endpoint', 'database', 'user', 'password']
