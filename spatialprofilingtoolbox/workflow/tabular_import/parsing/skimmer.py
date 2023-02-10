"""Source file parsing into the single-cell ADI schema."""
import importlib.resources
import re
from typing import Optional

from psycopg2 import sql
import pandas as pd

from spatialprofilingtoolbox.workflow.tabular_import.parsing.cell_manifests import \
    CellManifestsParser
from spatialprofilingtoolbox.workflow.tabular_import.parsing.channels import \
    ChannelsPhenotypesParser
from spatialprofilingtoolbox.workflow.tabular_import.parsing.cell_manifest_set import \
    CellManifestSetParser
from spatialprofilingtoolbox.workflow.tabular_import.parsing.samples import SamplesParser
from spatialprofilingtoolbox.workflow.tabular_import.parsing.subjects import SubjectsParser
from spatialprofilingtoolbox.workflow.tabular_import.parsing.sample_stratification import \
    SampleStratificationCreator
from spatialprofilingtoolbox.workflow.tabular_import.parsing.interventions import \
    InterventionsParser
from spatialprofilingtoolbox.workflow.tabular_import.parsing.diagnosis import DiagnosisParser
from spatialprofilingtoolbox.workflow.tabular_import.parsing.study import StudyParser
from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class DataSkimmer(DatabaseConnectionMaker):
    """
    Orchestration of source file parsing into single cell ADI schema database
    for a bundle of source files.
    """
    def __init__(self, database_config_file: Optional[str] = None):
        super().__init__(database_config_file=database_config_file)
        self.record_counts = {}

    def normalize(self, name):
        return re.sub(r'[ \-]', '_', name).lower()

    def retrieve_record_counts(self, cursor, fields):
        record_counts = {}
        table_names = sorted(list(set(fields['Table'])))
        table_names = [self.normalize(t) for t in table_names]
        for table in table_names:
            query = sql.SQL(
                'SELECT COUNT(*) FROM {} ;').format(sql.Identifier(table))
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
            difference_str = f'{sign}{absolute_difference}'
            padded = f"{difference_str:<13}"
            logger.debug('%s %s', padded, table)

    def parse(self, files):
        if not self.is_connected():
            logger.debug(
                'No database connection was initialized. Skipping semantic parse.')
            return
        with importlib.resources.path('adiscstudies', 'fields.tsv') as path:
            fields = pd.read_csv(path, sep='\t', na_filter=False)

        self.cache_all_record_counts(self.get_connection(), fields)

        study_name = StudyParser(fields).parse(
            self.get_connection(),
            files['study'],
        )
        SubjectsParser(fields).parse(
            self.get_connection(),
            files['subjects'],
        )
        DiagnosisParser(fields).parse(
            self.get_connection(),
            files['diagnosis'],
        )
        InterventionsParser(fields).parse(
            self.get_connection(),
            files['interventions'],
        )
        SamplesParser(fields).parse(
            self.get_connection(),
            files['samples'],
            study_name,
        )
        CellManifestSetParser(fields).parse(
            self.get_connection(),
            files['file manifest'],
            study_name,
        )
        chemical_species_identifiers_by_symbol = ChannelsPhenotypesParser(fields).parse(
            self.get_connection(),
            files['channels'],
            files['phenotypes'],
            study_name,
        )
        CellManifestsParser(fields, channels_file=files['channels']).parse(
            self.get_connection(),
            files['file manifest'],
            chemical_species_identifiers_by_symbol,
        )
        SampleStratificationCreator.create_sample_stratification(
            self.get_connection())

        self.report_record_count_changes(self.get_connection(), fields)
