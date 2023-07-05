"""
A context manager from accessing the backend SPT database, from inside library
functions.
"""
from os.path import exists
from os.path import abspath
from os.path import expanduser

from psycopg2 import connect
from psycopg2.extensions import connection as Psycopg2Connection
from psycopg2 import Error as Psycopg2Error

from spatialprofilingtoolbox.db.credentials import get_credentials_from_environment
from spatialprofilingtoolbox.db.credentials import retrieve_credentials_from_file
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class DatabaseConnectionMaker:
    """
    Provides a psycopg2 Postgres database connection. Takes care of connecting
    and disconnecting.
    """
    connection: Psycopg2Connection

    def __init__(self, database_config_file: str | None=None):
        if database_config_file is not None:
            credentials = retrieve_credentials_from_file(database_config_file)
        else:
            credentials = get_credentials_from_environment()
        try:
            self.connection = connect(
                dbname=credentials.database,
                host=credentials.endpoint,
                user=credentials.user,
                password=credentials.password,
            )
        except Psycopg2Error:
            message = 'Failed to connect to database: %s %s'
            logger.warning(message, credentials.endpoint, credentials.database)
            logger.info('Trying with alternative database name.')
            try:
                self.connection = connect(
                    dbname='postgres',
                    host=credentials.endpoint,
                    user=credentials.user,
                    password=credentials.password,
                )
            except Psycopg2Error as exception:
                logger.error(message, credentials.endpoint, 'postgres')
                raise exception

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
