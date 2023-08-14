"""Source file parsing into the single-cell ADI schema."""
from importlib.resources import as_file
from importlib.resources import files
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
from spatialprofilingtoolbox import DatabaseConnectionMaker
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class DataSkimmer(DatabaseConnectionMaker):
    """Orchestration of source file parsing into single cell ADI schema database
    for a bundle of source files.
    """
    record_counts: dict[str, int]

    def __init__(self, database_config_file: Optional[str] = None):
        super().__init__(database_config_file=database_config_file)
        self.record_counts = {}

    def _normalize(self, name):
        return re.sub(r'[ \-]', '_', name).lower()

    def _retrieve_record_counts(self, cursor, fields) -> dict[str, int]:
        record_counts: dict[str, int] = {}
        table_names = sorted(list(set(fields['Table'])))
        table_names = [self._normalize(t) for t in table_names]
        for table in table_names:
            query = sql.SQL('SELECT COUNT(*) FROM {} ;').format(sql.Identifier(table))
            cursor.execute(query)
            rows = cursor.fetchall()
            record_counts[table] = rows[0][0]
        return record_counts

    def _cache_all_record_counts(self, connection, fields):
        cursor = connection.cursor()
        self.record_counts = self._retrieve_record_counts(cursor, fields)
        cursor.close()

    def _report_record_count_changes(self, connection, fields):
        cursor = connection.cursor()
        current_counts = self._retrieve_record_counts(cursor, fields)
        changes = {
            table: current_counts[table] - self.record_counts[str(table)]
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

    def parse(self, _files) -> None:
        if not self.is_connected():
            message = 'No database connection was initialized. Skipping semantic parse.'
            logger.debug(message)
            return
        with as_file(files('adiscstudies').joinpath('fields.tsv')) as path:
            fields = pd.read_csv(path, sep='\t', na_filter=False)

        self._cache_all_record_counts(self.get_connection(), fields)

        study_name = StudyParser(fields).parse(self.get_connection(), _files['study'])
        conn = self.get_connection()
        SubjectsParser(fields).parse(conn, _files['subjects'])
        DiagnosisParser(fields).parse(conn, _files['diagnosis'])
        InterventionsParser(fields).parse(conn, _files['interventions'])
        SamplesParser(fields).parse(conn, _files['samples'], study_name)
        CellManifestSetParser(fields).parse(conn, _files['file manifest'], study_name)
        chemical_species_identifiers_by_symbol = ChannelsPhenotypesParser(fields).parse(
            conn,
            _files['channels'],
            _files['phenotypes'],
            study_name,
        )
        CellManifestsParser(fields, channels_file=_files['channels']).parse(
            conn,
            _files['file manifest'],
            chemical_species_identifiers_by_symbol,
        )
        SampleStratificationCreator.create_sample_stratification(conn)
        self._report_record_count_changes(conn, fields)
