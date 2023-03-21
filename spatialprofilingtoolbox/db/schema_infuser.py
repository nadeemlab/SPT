"""
Utility to write the single-cell studies "ADI" SQL schema, plus performance-
and SPT-related tweaks, into a Postgresql instance.
"""
import importlib.resources
import re
from typing import Optional

import pandas as pd
import datetime

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.verbose_sql_execution import verbose_sql_execute
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
from spatialprofilingtoolbox.workflow.common.export_features import ADIFeaturesUploader

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
        self.link_fraction_views()

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

    def link_fraction_views(self):
        """
        Transcribe phenotype fraction features in features system
        """
        connection = self.get_connection()
        cursor = connection.cursor()
        feat_extr_query = """
            SELECT t1.marker_symbol, t1.measurement_study, t1.average_percent, t1.stratum_identifier, t2.sample
            FROM fraction_stats  t1
            LEFT JOIN (
                SELECT stratum_identifier, MIN(sample) as sample
                FROM sample_strata
                GROUP BY stratum_identifier
            ) t2 ON t1.stratum_identifier = t2.stratum_identifier;
            """
        fraction_features = pd.read_sql(feat_extr_query, connection)
        cursor.close()
        connection.commit()
        for study in fraction_features['measurement_study'].unique():
            study_name = study.replace(' - measurement', '')
            fraction_features_study = fraction_features[fraction_features.measurement_study == study]
            with ADIFeaturesUploader(
                    database_config_file=self.database_config_file,
                    data_analysis_study=self.insert_new_data_analysis_study(study_name),
                    derivation_method=self.describe_feature_derivation_method(),
                    specifier_number=1,
            ) as feature_uploader:
                values = fraction_features_study['average_percent'].values
                # TODO: remove hardcode
                subjects = fraction_features_study['sample']
                specifiers_lists = fraction_features_study['marker_symbol'].values
                for value, subject, specifiers_list in (zip(values, subjects, specifiers_lists)):
                    feature_uploader.stage_feature_value((specifiers_list,), subject, value)

    def describe_feature_derivation_method(self):
        return '''
        For a given cell phenotype (first specifier), the average number of cells of a second phenotype (second specifier) within a specified radius (third specifier).
        '''.lstrip().rstrip()

    def insert_new_data_analysis_study(self, study_name):
        timestring = str(datetime.datetime.now())
        name = study_name + f'{study_name} : fraction calculation : {timestring}'
        with DatabaseConnectionMaker(self.database_config_file) as dcm:
            connection = dcm.get_connection()
            cursor = connection.cursor()
            cursor.execute('''
            INSERT INTO data_analysis_study(name)
            VALUES (%s) ;
            INSERT INTO study_component(primary_study, component_study)
            VALUES (%s, %s) ;
            ''', (name, study_name, name))
            cursor.close()
            connection.commit()
        return name
