"""
Utility to write the single-cell studies "ADI" SQL schema, plus performance-
and SPT-related tweaks, into a Postgresql instance.
"""
import importlib.resources
import re
from typing import Optional

import pandas as pd

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.verbose_sql_execution import verbose_sql_execute
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class SchemaInfuser(DatabaseConnectionMaker):
    """Create single cell database schema in a given database."""
    def __init__(self, database_config_file: Optional[str] = None):
        super().__init__(database_config_file=database_config_file)

    def setup_schema(self, force=False):
        logger.info(
            'This creation tool assumes that the database itself and users are already set up.')
        if force is True:
            self.verbose_sql_execute(('drop_views.sql', 'drop views of main schema'))
            self.verbose_sql_execute((None, 'drop tables from main schema'),
                                     contents=self.create_drop_tables())
        self.verbose_sql_execute(('schema.sql', 'create tables from main schema'),
                                 source_package='adiscstudies')
        self.verbose_sql_execute(('performance_tweaks.sql', 'tweak main schema'))
        self.verbose_sql_execute(('create_views.sql', 'create views of main schema'))
        self.verbose_sql_execute(('grant_on_tables.sql', 'grant appropriate access to users'))

    def normalize(self, name):
        return re.sub(r'[ \-]', '_', name).lower()

    def get_schema_documentation_tables(self):
        return [
            f'reference_{tablename}'
            for tablename in ['tables', 'fields', 'entities', 'properties', 'values']
        ]

    def create_drop_tables(self):
        with importlib.resources.path('adiscstudies', 'fields.tsv') as path:
            fields = pd.read_csv(path, sep='\t', keep_default_na=False)
        table_names = sorted(list(set(self.normalize(t) for t in fields['Table'])))
        table_names = table_names + self.get_schema_documentation_tables() + ['sample_strata']
        return '\n'.join([
            f'DROP TABLE IF EXISTS {t} CASCADE ; ' for t in table_names
        ])

    def refresh_views(self):
        self.verbose_sql_execute(('refresh_views.sql', 'refresh views of main schema'),
                                  verbosity='silent')

    def recreate_views(self):
        self.verbose_sql_execute(('drop_views.sql', 'drop views of main schema'))
        self.verbose_sql_execute(('create_views.sql', 'create views of main schema'),
                                 verbosity='itemize')
        self.verbose_sql_execute(('grant_on_tables.sql', 'grant appropriate access to users'))

    def verbose_sql_execute(self, filename_description,
                            source_package='spatialprofilingtoolbox.db.data_model',
                            **kwargs):
        verbose_sql_execute(filename_description, self.get_connection(),
                            source_package=source_package, **kwargs)
