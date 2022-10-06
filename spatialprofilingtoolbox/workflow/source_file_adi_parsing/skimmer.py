import importlib.resources
import re

import psycopg2
from psycopg2 import sql
import pandas as pd

from ...standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)

from ...db.database_connection import DatabaseConnectionMaker
from ...db.source_file_parser_interface import SourceToADIParser
from ...db.source_file_parser_interface import DBBackend
from ...db.verbose_sql_execution import verbose_sql_execute
from .subjects import SubjectsParser
from .samples import SamplesParser
from .cellmanifestset import CellManifestSetParser
from .channels import ChannelsPhenotypesParser
from .cellmanifests import CellManifestsParser


class DataSkimmer:
    def __init__(self, database_config_file: str=None, db_backend=DBBackend.POSTGRES):
        if db_backend != DBBackend.POSTGRES:
            raise ValueError('Only DBBackend.POSTGRES is supported.')
        self.db_backend = db_backend
        dcm = DatabaseConnectionMaker(database_config_file)
        self.connection = dcm.get_connection()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.connection:
            self.connection.close()

    def get_connection(self):
        return self.connection

    def normalize(self, name):
        return re.sub('[ \-]', '_', name).lower()

    def retrieve_record_counts(self, cursor, fields):
        record_counts = {}
        tablenames = sorted(list(set(fields['Table'])))
        tablenames = [self.normalize(t) for t in tablenames]
        for table in tablenames:
            query = sql.SQL('SELECT COUNT(*) FROM {} ;').format(sql.Identifier(table))
            cursor.execute(query)
            rows = cursor.fetchall()
            record_counts[table] = rows[0][0]
        return record_counts

    def cache_all_record_counts(self, connection, fields):
        cursor = connection.cursor()
        self.record_counts = self.retrieve_record_counts(cursor, fields)
        cursor.close()

    def report_record_count_changes(self, connection, fields):
        cursor = connection.cursor()
        current_counts = self.retrieve_record_counts(cursor, fields)
        changes = {
            table: current_counts[table] - self.record_counts[table]
            for table in sorted(current_counts.keys())
        }
        cursor.close()
        logger.debug('Record count changes:')
        for table in sorted(changes.keys()):
            difference = changes[table]
            sign = '+' if difference >= 0 else '-'
            absolute_difference = difference if difference > 0 else -1*difference
            difference_str = "{:<13}".format('%s%s' % (sign, absolute_difference))
            logger.debug('%s %s', difference_str, table)

    def parse(
            self,
            dataset_design = None,
            computational_design = None,
            file_manifest_file = None,
            elementary_phenotypes_file = None,
            composite_phenotypes_file = None,
            outcomes_file = None,
            compartments_file = None,
            subjects_file = None,
            **kwargs,
        ):
        if not self.connection:
            logger.debug('No database connection was initialized. Skipping semantic parse.')
            return
        with importlib.resources.path('adisinglecell', 'fields.tsv') as path:
            fields = pd.read_csv(path, sep='\t', na_filter=False)

        self.cache_all_record_counts(self.connection, fields)

        age_at_specimen_collection = SubjectsParser().parse(
            self.connection,
            fields,
            subjects_file,
        )
        samples_file = outcomes_file
        SamplesParser().parse(
            self.connection,
            fields,
            samples_file,
            age_at_specimen_collection,
            file_manifest_file,
        )
        CellManifestSetParser().parse(
            self.connection,
            fields,
            file_manifest_file,
        )
        chemical_species_identifiers_by_symbol = ChannelsPhenotypesParser().parse(
            self.connection,
            fields,
            file_manifest_file,
            elementary_phenotypes_file,
            composite_phenotypes_file,
        )
        CellManifestsParser().parse(
            self.connection,
            fields,
            dataset_design,
            computational_design,
            file_manifest_file,
            chemical_species_identifiers_by_symbol,
        )

        self.report_record_count_changes(self.connection, fields)
