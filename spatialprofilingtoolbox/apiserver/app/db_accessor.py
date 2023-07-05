"""
A context manager for accessing the backend SPT database, from the API service.
"""
import time

from psycopg2 import connect
from psycopg2.extensions import connection as Psycopg2Connection
from psycopg2.extensions import cursor as Psycopg2Cursor
from psycopg2 import OperationalError

from spatialprofilingtoolbox.db.credentials import DBCredentials
from spatialprofilingtoolbox.db.credentials import get_credentials_from_environment
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class DBAccessor:
    """
    Provides a psycopg2 Postgres database connection. Takes care of connecting
    and disconnecting.
    """
    connection: Psycopg2Connection
    cursor: Psycopg2Cursor

    def get_connection(self):
        return self.connection

    def get_cursor(self):
        return self.cursor

    def __enter__(self):
        credentials = get_credentials_from_environment()
        try:
            self._make_connection_and_cursor(credentials)
        except OperationalError:
            credentials = get_credentials_from_environment(database_name='postgres')
            self._make_connection_and_cursor(credentials)
        return self, self.get_connection(), self.get_cursor()

    def _make_connection_and_cursor(self, credentials: DBCredentials):
        self.connection = connect(
            dbname=credentials.database,
            host=credentials.endpoint,
            user=credentials.user,
            password=credentials.password,
        )
        self.cursor = self.connection.cursor()

    def is_ready(self):
        return self.connection is not None

    def __exit__(self, exception_type, exception_value, traceback):
        self.cursor.close()
        self.connection.commit()
        self.connection.close()


def wait_for_database_ready():
    while True:
        try:
            if _check_database_is_ready():
                break
        except OperationalError:
            logger.debug('Database is not ready.')
            time.sleep(2.0)
    logger.info('Database is ready.')


def _check_database_is_ready() -> bool:
    with DBAccessor() as (db_accessor, _, _):
        if db_accessor.is_ready():
            return True
    return False
