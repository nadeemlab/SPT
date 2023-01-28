"""Source file parsing into the single-cell ADI schema."""
import importlib.resources
import re
from typing import Optional

from psycopg2 import sql
import pandas as pd

from spatialprofilingtoolbox.workflow.source_file_adi_parsing.cell_manifests import \
    CellManifestsParser
from spatialprofilingtoolbox.workflow.source_file_adi_parsing.channels import \
    ChannelsPhenotypesParser
from spatialprofilingtoolbox.workflow.source_file_adi_parsing.cell_manifest_set import \
    CellManifestSetParser
from spatialprofilingtoolbox.workflow.source_file_adi_parsing.samples import SamplesParser
from spatialprofilingtoolbox.workflow.source_file_adi_parsing.subjects import SubjectsParser
from spatialprofilingtoolbox.workflow.source_file_adi_parsing.sample_stratification import \
    SampleStratificationCreator
from spatialprofilingtoolbox.workflow.source_file_adi_parsing.interventions import \
    InterventionsParser
from spatialprofilingtoolbox.workflow.source_file_adi_parsing.diagnosis import DiagnosisParser
from spatialprofilingtoolbox.workflow.source_file_adi_parsing.study import StudyParser
from spatialprofilingtoolbox.db.source_file_parser_interface import DBBackend
from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class DataSkimmer(DatabaseConnectionMaker):
    """
    Orchestration of source file parsing into single cell ADI schema database
    for a bundle of source files.
    """
    def __init__(self, database_config_file: Optional[str] = None, db_backend=DBBackend.POSTGRES):
        if db_backend != DBBackend.POSTGRES:
            raise ValueError('Only DBBackend.POSTGRES is supported.')
        self.db_backend = db_backend
        super(DataSkimmer, self).__init__(
            database_config_file=database_config_file)
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

    def parse(
        self,
        dataset_design=None,
        computational_design=None,
        file_manifest_file=None,
        elementary_phenotypes_file=None,
        composite_phenotypes_file=None,
        outcomes_file=None,
        compartments_file=None,
        subjects_file=None,
        study_file=None,
        diagnosis_file=None,
        interventions_file=None,
        **kwargs, # pylint: disable=unused-argument
    ):
        if not self.is_connected():
            logger.debug(
                'No database connection was initialized. Skipping semantic parse.')
            return
        with importlib.resources.path('adiscstudies', 'fields.tsv') as path:
            fields = pd.read_csv(path, sep='\t', na_filter=False)

        self.cache_all_record_counts(self.get_connection(), fields)

        study_name = StudyParser().parse(
            self.get_connection(),
            fields,
            study_file,
        )
        SubjectsParser().parse(
            self.get_connection(),
            fields,
            subjects_file,
        )
        DiagnosisParser().parse(
            self.get_connection(),
            fields,
            diagnosis_file,
        )
        InterventionsParser().parse(
            self.get_connection(),
            fields,
            interventions_file,
        )
        samples_file = outcomes_file
        SamplesParser().parse(
            self.get_connection(),
            fields,
            samples_file,
            study_name,
        )
        CellManifestSetParser().parse(
            self.get_connection(),
            fields,
            file_manifest_file,
            study_name,
        )
        chemical_species_identifiers_by_symbol = ChannelsPhenotypesParser().parse(
            self.get_connection(),
            fields,
            elementary_phenotypes_file,
            composite_phenotypes_file,
            study_name,
        )
        CellManifestsParser().parse(
            self.get_connection(),
            dataset_design,
            computational_design,
            file_manifest_file,
            chemical_species_identifiers_by_symbol,
        )
        SampleStratificationCreator.create_sample_stratification(
            self.get_connection())

        self.report_record_count_changes(self.get_connection(), fields)
