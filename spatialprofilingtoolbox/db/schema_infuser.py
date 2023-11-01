""" Utility to write the single-cell studies "ADI" SQL schema, plus performance- and SPT-related
tweaks, into a Postgresql instance.
"""
from importlib.resources import as_file
from importlib.resources import files
import re

import pandas as pd
from psycopg2 import Error as Psycopg2Error
from psycopg2.errors import UndefinedTable

from spatialprofilingtoolbox.db.database_connection import create_database
from spatialprofilingtoolbox.db.credentials import metaschema_database
from spatialprofilingtoolbox.db.verbose_sql_execution import verbose_sql_execute
from spatialprofilingtoolbox.db.fractions_transcriber import transcribe_fraction_features
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class SchemaInfuser:
    """Create single cell database schema in a given database."""
    database_config_file: str | None
    study: str | None

    def __init__(self, database_config_file: str | None = None, study: str | None = None):
        self.database_config_file = database_config_file
        self.study = study

    def setup_lightweight_metaschema(self, force=False):
        create_database(self.database_config_file, metaschema_database())
        if force:
            try:
                self._verbose_sql_execute(('drop_metaschema.sql', 'drop metaschema tables'))
            except UndefinedTable:
                pass
        self._verbose_sql_execute(
            ('metaschema.sql', 'create tables from lightweight metaschema'),
        )
        try:
            self._verbose_sql_execute(('grant_on_tables.sql', 'grant appropriate access to users'))
        except Psycopg2Error as exception:
            logger.warning('Could not run grant privileges script. Possibly users are not set up.')
            logger.warning(exception)

    def setup_schema(self, force=False):
        message = 'This creation tool assumes that the database itself and users are already setup.'
        logger.info(message)
        if force:
            self._verbose_sql_execute(('drop_views.sql', 'drop views of main schema'))
            self._verbose_sql_execute(
                (None, 'drop tables from main schema'),
                contents=self.create_drop_tables(),
            )
        logger.info('Executing schema.sql contents.')
        self._verbose_sql_execute(
            ('schema.sql', 'create tables from main schema'),
            source_package='adiscstudies',
            verbosity='silent',
        )
        self._verbose_sql_execute(('performance_tweaks.sql', 'tweak main schema'))
        logger.info('Executing create_views.sql contents.')
        self._verbose_sql_execute(('create_views.sql', 'create views of main schema'), verbosity='silent')
        try:
            self._verbose_sql_execute(('grant_on_tables.sql', 'grant appropriate access to users'))
        except Psycopg2Error as exception:
            logger.warning('Could not run grant privileges script. Possibly users are not set up.')
            logger.warning(exception)

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
        if self.study is not None:
            self._verbose_sql_execute(
                ('refresh_views.sql', 'refresh views of main schema'),
                verbosity='itemize',
            )
            transcribe_fraction_features(self.database_config_file, self.study)

    def recreate_views(self):
        self._verbose_sql_execute(('drop_views.sql', 'drop views of main schema'))
        self._verbose_sql_execute(
            ('create_views.sql', 'create views of main schema'),
            verbosity='itemize',
        )
        self._verbose_sql_execute(('grant_on_tables.sql', 'grant appropriate access to users'))

    def _verbose_sql_execute(self,
        filename_description,
        source_package='spatialprofilingtoolbox.db.data_model',
        contents: str | None = None,
        **kwargs,
    ):
        verbose_sql_execute(
            filename_description,
            self.database_config_file,
            source_package=source_package,
            contents=contents,
            study=self.study,
            **kwargs,
        )
