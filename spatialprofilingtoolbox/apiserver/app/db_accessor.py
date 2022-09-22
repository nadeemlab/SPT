import os

import psycopg2


class DBAccessor:
    def __init__(self):
        self.connection = None

    def get_connection(self):
        return self.connection

    def __enter__(self):
        variables = [
            'SINGLE_CELL_DATABASE_HOST',
            'SINGLE_CELL_DATABASE_USER',
            'SINGLE_CELL_DATABASE_PASSWORD',
        ]
        unfound = [v for v in variables if not v in os.environ]
        if len(unfound) > 0:
            message = 'Did not find: %s' % str(unfound)
            raise EnvironmentError(message)

        dbname = 'scstudies'
        if 'USE_ALTERNATIVE_TESTING_DATABASE' in os.environ:
            dbname = 'postgres'
        if 'USE_LEGACY_DATABASE' in os.environ:
            dbname = 'pathstudies'

        self.connection = psycopg2.connect(
            dbname=dbname,
            host=os.environ['SINGLE_CELL_DATABASE_HOST'],
            user=os.environ['SINGLE_CELL_DATABASE_USER'],
            password=os.environ['SINGLE_CELL_DATABASE_PASSWORD'],
        )
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if not self.connection is None:
            self.connection.close()
