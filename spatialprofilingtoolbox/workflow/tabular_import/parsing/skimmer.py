"""Source file parsing into the single-cell ADI schema."""
from importlib.resources import as_file
from importlib.resources import files
import re
import json

from psycopg2 import sql
from psycopg2 import connect
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
from spatialprofilingtoolbox.db.database_connection import DBConnection
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import create_database
from spatialprofilingtoolbox.db.modify_constraints import DBConstraintsToggling
from spatialprofilingtoolbox.db.modify_constraints import toggle_constraints
from spatialprofilingtoolbox.db.schema_infuser import SchemaInfuser
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class DataSkimmer:
    """Orchestration of source file parsing into single cell ADI schema database
    for a bundle of source files.
    """
    database_config_file: str | None
    record_counts: dict[str, int]

    def __init__(self, database_config_file: str | None = None):
        self.database_config_file = database_config_file
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

    @staticmethod
    def _sanitize_token(token: str) -> str:
        return re.sub(r'[ \-]', '_', token).lower()

    def _register_study(self, study_file: str) -> str:
        with open(study_file, 'rt', encoding='utf-8') as file:
            study = json.loads(file.read())
            study_name = study['Study name']

        if self._study_is_registered(study_name):
            raise ValueError('The study "%s" is already registered.', study_name)

        database_name = self._sanitize_token(study_name)
        self._create_database(database_name)
        self._register_study_database_name(study_name, database_name)
        self._create_schema(study_name)
        return study_name

    def _create_database(self, database_name: str) -> None:
        create_database(self.database_config_file, database_name)

    def _register_study_database_name(self, study_name: str, database_name: str) -> None:
        with DBCursor(database_config_file=self.database_config_file) as cursor:
            cursor.execute('INSERT INTO study_lookup VALUES (%s, %s) ;', (study_name, database_name))

    def _create_schema(self, study: str) -> None:
        infuser = SchemaInfuser(database_config_file=self.database_config_file, study=study)
        infuser.setup_schema()

    def _study_is_registered(self, study_name: str) -> bool:
        with DBCursor(database_config_file=self.database_config_file) as cursor:
            cursor.execute('SELECT * FROM study_lookup WHERE study=%s;', (study_name,))
            rows = cursor.fetchall()
            if len(rows) > 0:
                return True
            return False

    def parse(self, _files) -> None:
        study_name = self._register_study(_files['study'])
        with as_file(files('adiscstudies').joinpath('fields.tsv')) as path:
            fields = pd.read_csv(path, sep='\t', na_filter=False)

        toggle_constraints(
            self.database_config_file,
            study_name,
            state=DBConstraintsToggling.DROP,
        )

        with DBConnection(database_config_file=self.database_config_file, study=study_name) as connection:
            self._cache_all_record_counts(connection, fields)
            StudyParser(fields).parse(connection, _files['study'])
            SubjectsParser(fields).parse(connection, _files['subjects'])
            DiagnosisParser(fields).parse(connection, _files['diagnosis'])
            InterventionsParser(fields).parse(connection, _files['interventions'])
            SamplesParser(fields).parse(connection, _files['samples'], study_name)
            CellManifestSetParser(fields).parse(connection, _files['file manifest'], study_name)
            chemical_species_identifiers_by_symbol = ChannelsPhenotypesParser(fields).parse(
                connection,
                _files['channels'],
                _files['phenotypes'],
                study_name,
            )
            CellManifestsParser(fields, channels_file=_files['channels']).parse(
                connection,
                _files['file manifest'],
                chemical_species_identifiers_by_symbol,
            )
            SampleStratificationCreator.create_sample_stratification(connection)
            self._report_record_count_changes(connection, fields)

        toggle_constraints(
            self.database_config_file,
            study_name,
            state=DBConstraintsToggling.RECREATE,
        )
