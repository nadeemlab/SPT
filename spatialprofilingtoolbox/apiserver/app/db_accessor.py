"""
A context manager for accessing the backend SPT database, from the API service.
"""
from os import environ

from psycopg2 import connect
from psycopg2.extensions import connection as Psycopg2Connection
from psycopg2.extensions import cursor as Psycopg2Cursor


class DBAccessor:
    """
    Provides a psycopg2 Postgres database connection. Takes care of connecting
    and disconnecting.
    """
    connection: Psycopg2Connection
    cursor: Psycopg2Cursor

    def __init__(self):
        self.endpoint = None
        self.database = None
        self.user = None
        self.password = None

    def get_connection(self):
        return self.connection

    def get_cursor(self):
        return self.cursor

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

        self.endpoint = environ['SINGLE_CELL_DATABASE_HOST']
        self.database = dbname
        self.user = environ['SINGLE_CELL_DATABASE_USER']
        self.password = environ['SINGLE_CELL_DATABASE_PASSWORD']

        self.connection = connect(
            dbname=dbname,
            host=environ['SINGLE_CELL_DATABASE_HOST'],
            user=environ['SINGLE_CELL_DATABASE_USER'],
            password=environ['SINGLE_CELL_DATABASE_PASSWORD'],
        )
        self.cursor = self.connection.cursor()
        return self, self.connection, self.cursor

    def get_database_config_file_contents(self):
        return f'''
[database-credentials]
endpoint =  {self.endpoint}
database = {self.database}
user = {self.user}
password = {self.password}
'''

    def __exit__(self, exception_type, exception_value, traceback):
        self.cursor.close()
        self.connection.commit()
        self.connection.close()
