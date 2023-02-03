"""
A context manager for accessing the backend SPT database, from the API service.
"""
from os import environ

from psycopg2 import connect
from psycopg2.extensions import connection as Psycopg2Connection


class DBAccessor:
    """
    Provides a psycopg2 Postgres database connection. Takes care of connecting
    and disconnecting.
    """
    connection: Psycopg2Connection

    def get_connection(self):
        return self.connection

    def __enter__(self):
        variables = [
            'SINGLE_CELL_DATABASE_HOST',
            'SINGLE_CELL_DATABASE_USER',
            'SINGLE_CELL_DATABASE_PASSWORD',
        ]
        unfound = [v for v in variables if not v in environ]
        if len(unfound) > 0:
            raise EnvironmentError(f'Did not find: {str(unfound)}')

        dbname = 'scstudies'
        if 'USE_ALTERNATIVE_TESTING_DATABASE' in environ:
            dbname = 'postgres'
        if 'USE_LEGACY_DATABASE' in environ:
            dbname = 'pathstudies'

        self.connection = connect(
            dbname=dbname,
            host=environ['SINGLE_CELL_DATABASE_HOST'],
            user=environ['SINGLE_CELL_DATABASE_USER'],
            password=environ['SINGLE_CELL_DATABASE_PASSWORD'],
        )
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if not self.connection is None:
            self.connection.close()
