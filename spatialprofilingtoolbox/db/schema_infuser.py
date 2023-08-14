""" Utility to write the single-cell studies "ADI" SQL schema, plus performance- and SPT-related
tweaks, into a Postgresql instance.
"""
from importlib.resources import as_file
from importlib.resources import files
import re
from typing import Optional

import pandas as pd

from spatialprofilingtoolbox import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.verbose_sql_execution import verbose_sql_execute
from spatialprofilingtoolbox.db.fractions_transcriber import transcribe_fraction_features
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class SchemaInfuser(DatabaseConnectionMaker):
    """Create single cell database schema in a given database."""
    def __init__(self, database_config_file: Optional[str] = None):
        super().__init__(database_config_file=database_config_file)

    def setup_schema(self, force=False):
        message = 'This creation tool assumes that the database itself and users are already setup.'
        logger.info(message)
        if force:
            self.verbose_sql_execute(('drop_views.sql', 'drop views of main schema'))
            self.verbose_sql_execute(
                (None, 'drop tables from main schema'),
                contents=self.create_drop_tables(),
            )
        self.verbose_sql_execute(
            ('schema.sql', 'create tables from main schema'),
            source_package='adiscstudies',
        )
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
        with as_file(files('adiscstudies').joinpath('fields.tsv')) as path:
            fields = pd.read_csv(path, sep='\t', keep_default_na=False)
        table_names = sorted(list(set(self.normalize(t) for t in fields['Table'])))
        performance_extras = ['sample_strata', 'pending_feature_computation', 'umap_plots']
        table_names = table_names + self.get_schema_documentation_tables() + performance_extras
        return '\n'.join([
            f'DROP TABLE IF EXISTS {t} CASCADE ; ' for t in table_names
        ])

    def refresh_views(self):
        self.verbose_sql_execute(
            ('refresh_views.sql', 'refresh views of main schema'),
            verbosity='itemize',
        )
        transcribe_fraction_features(self)

    def recreate_views(self):
        self.verbose_sql_execute(('drop_views.sql', 'drop views of main schema'))
        self.verbose_sql_execute(
            ('create_views.sql', 'create views of main schema'),
            verbosity='itemize',
        )
        self.verbose_sql_execute(('grant_on_tables.sql', 'grant appropriate access to users'))

    def verbose_sql_execute(self,
        filename_description,
        source_package='spatialprofilingtoolbox.db.data_model',
        **kwargs,
    ):
        verbose_sql_execute(
            filename_description,
            self.get_connection(),
            source_package=source_package,
            **kwargs,
        )
