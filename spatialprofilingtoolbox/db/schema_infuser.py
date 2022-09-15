import importlib.resources

import pandas as pd
import adisinglecell

from .database_connection import DatabaseConnectionMaker
from .verbose_sql_execution import verbose_sql_execute
from ..standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)


class SchemaInfuser:
    def __init__(self, database_config_file: str=None):
        dcm = DatabaseConnectionMaker(database_config_file)
        self.connection = dcm.get_connection()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.connection:
            self.connection.close()

    def get_connection(self):
        return self.connection

    def create_drop_tables(self):
        with importlib.resources.path('adisinglecell', 'fields.tsv') as path:
            fields = pd.read_csv(path, sep='\t', keep_default_na=False)
        tablenames = sorted(list(set([self.normalize(t) for t in fields['Table']])))
        return '\n'.join([
            'DROP TABLE IF EXISTS %s CASCADE ; ' % t
            for t in tablenames
        ])

    def create_tables(self, force=False):
        logger.info('This creation tool assumes that the database itself and users are already set up.')
        if force is True:
            verbose_sql_execute('drop_views.sql', self.get_connection(), description='drop views of main schema')
            verbose_sql_execute(None, self.get_connection(), description='drop tables from main schema', contents=self.create_drop_tables())

        verbose_sql_execute('schema.sql', self.get_connection(), description='create tables from main schema', source_package='adisinglecell')
        verbose_sql_execute('performance_tweaks.sql', self.get_connection(), description='tweak main schema')
        verbose_sql_execute('create_views.sql', self.get_connection(), description='create views of main schema')
        verbose_sql_execute('grant_on_tables.sql', self.get_connection(), description='grant appropriate access to users')

    def refresh_views(self):
        verbose_sql_execute('refresh_views.sql', self.get_connection(), description='create views of main schema', silent=True)

    def recreate_views(self):
        verbose_sql_execute('drop_views.sql', self.get_connection(), description='drop views of main schema')
        verbose_sql_execute('create_views.sql', self.get_connection(), description='create views of main schema', itemize=True)
        verbose_sql_execute('grant_on_tables.sql', self.get_connection(), description='grant appropriate access to users')
