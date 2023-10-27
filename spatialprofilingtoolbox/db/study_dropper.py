"""Drop a single study."""
import re

from psycopg2.extensions import connection as Pyscopg2Connection
from psycopg2.extensions import cursor as Pyscopg2Cursor

from spatialprofilingtoolbox.db.database_connection import DBConnection
from spatialprofilingtoolbox.db.check_tables import check_tables
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class StudyDropper:
    """Drop a single study."""

    connection: Pyscopg2Connection
    cursor: Pyscopg2Cursor
    study: str

    def __init__(self, connection: Pyscopg2Connection, study: str):
        self.connection = connection
        self.study = study
        self.cached_counts = None

    def __enter__(self):
        self.cursor = self.connection.cursor()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.cursor:
            self.cursor.close()

    def get_cursor(self):
        return self.cursor

    def cache_record_counts(self, counts):
        self.cached_counts = counts

    def report_record_count_change(self):
        _, counts = check_tables(self.get_cursor())
        cacheable = [
            (row[0], row[1]) for row in counts
        ]
        if self.cached_counts is None:
            self.cache_record_counts(cacheable)
            return
        for (table1, count1), (table2, count2) in zip(self.cached_counts, cacheable):
            if table1 != table2:
                logger.warning('Mismatched tablenames: %s, %s.', table1, table2)
            if count1 != count2:
                justified = table1.ljust(42, ' ')
                difference = str(count2 - count1)
                if not re.search('-', difference):
                    difference = '+' + difference
                logger.info('    %s %s', justified, difference)
        self.cache_record_counts(cacheable)

    @staticmethod
    def drop(database_config_file: str | None, study: str) -> None:
        """ Use this method as the entrypoint into this class' functionality."""
        with DBConnection(database_config_file=database_config_file, study=study) as connection:
            with StudyDropper(connection, study) as dropper:
                dropper.check_existence_of_study()
                dropper.drop_records()

    def check_existence_of_study(self):
        self.get_cursor().execute('SELECT * FROM study WHERE study_specifier=%s', (self.study,))
        if len(self.get_cursor().fetchall()) == 0:
            raise ValueError(f'Study "{self.study}" does not exist.')
        logger.info('Study "%s" exists.', self.study)

    def drop_records(self):
        self.report_record_count_change()
        self.drop_specially_queried_records()
        self.drop_substudies()

    def drop_specially_queried_records(self):
        for command in [
            self.drop_diagnostic_selection_criterion,
            self.cache_shape_file_identifiers,
            self.drop_histological_structure,
            self.drop_shape_file,
        ]:
            command()
            self.report_record_count_change()

    def drop_substudies(self):
        for command in [self.drop_data_analysis_study,
            self.drop_measurement_study,
            self.drop_study,
            self.drop_sample_strata,
            self.drop_subject,
            self.drop_specimen_collection_study,
            self.drop_study_component,
        ]:
            command()
            self.report_record_count_change()

    def drop_diagnostic_selection_criterion(self):
        logger.info('Dropping from diagnostic_selection_criterion, with cascade to '
                    'two_cohort_feature_association_test.')
        self.get_cursor().execute('''
        DELETE FROM diagnostic_selection_criterion dsc
        WHERE dsc.identifier IN (
            SELECT selection_criterion_1 FROM two_cohort_feature_association_test t1
            JOIN feature_specification fs ON fs.identifier=t1.feature_tested
            JOIN study_component sc ON sc.component_study=fs.study
            WHERE sc.primary_study=%s
            UNION
            SELECT selection_criterion_2 FROM two_cohort_feature_association_test t2
            JOIN feature_specification fs ON fs.identifier=t2.feature_tested
            JOIN study_component sc ON sc.component_study=fs.study
            WHERE sc.primary_study=%s
        ) ;
        ''', (self.study, self.study,))

    def cache_shape_file_identifiers(self):
        logger.info('Caching the shape_file identifiers for records to be deleted, '
                    'to avoid orphaning them.')
        self.get_cursor().execute('''
        CREATE MATERIALIZED VIEW temporary_shape_files_to_be_deleted
        AS
        SELECT hsi.shape_file as shape_file_identifier FROM histological_structure_identification hsi
        JOIN data_file df ON df.sha256_hash=hsi.data_source
        JOIN specimen_data_measurement_process sdmp ON sdmp.identifier=df.source_generation_process
        JOIN study_component sc ON sc.component_study=sdmp.study
        WHERE sc.primary_study=%s
        WITH DATA
        ;
        ''', (self.study,))

    def drop_histological_structure(self):
        logger.info('Dropping histological_structure records. Should cascade upon '
                    'expression_quantification and histological_structure_identification.')
        self.get_cursor().execute('''
        DELETE FROM histological_structure hs
        WHERE hs.identifier IN (
            SELECT hsi.histological_structure FROM histological_structure_identification hsi
            JOIN data_file df ON df.sha256_hash=hsi.data_source
            JOIN specimen_data_measurement_process sdmp ON sdmp.identifier=df.source_generation_process
            JOIN study_component sc ON sc.component_study=sdmp.study
            WHERE sc.primary_study=%s
        ) ;
        ''', (self.study,))

    def drop_shape_file(self):
        logger.info('Dropping shape_file records.')
        self.get_cursor().execute('''
        DELETE FROM shape_file sf
        WHERE sf.identifier IN
            ( SELECT shape_file_identifier FROM temporary_shape_files_to_be_deleted )
        ;
        ''')
        self.get_cursor().execute('''
        DROP MATERIALIZED VIEW temporary_shape_files_to_be_deleted ;
        ''')

    def drop_data_analysis_study(self):
        logger.info('Dropping data_analysis_study, with cascading to cell_phenotype_criterion, '
                   'feature_specification, feature_specifier, quantitative_feature_value, and '
                   'two_cohort_feature_association_test.')
        self.get_cursor().execute('''
        DELETE FROM data_analysis_study das
        WHERE das.name IN (
            SELECT sc.component_study FROM study_component sc
            WHERE sc.primary_study=%s
        ) ;
        ''', (self.study,))

    def drop_measurement_study(self):
        logger.info('Dropping specimen_measurement_study, with cascading to '
                    'biological_marking_system, specimen_data_measurement_process, and data_file.')
        self.get_cursor().execute('''
        DELETE FROM specimen_measurement_study sms
        WHERE sms.name IN (
            SELECT sc.component_study FROM study_component sc
            WHERE sc.primary_study=%s
        ) ;
        ''', (self.study,))

    def drop_study(self):
        logger.info('Dropping "study" record, with cascading to publication, author, and '
                    'study_contact_person.')
        self.get_cursor().execute('''
        DELETE FROM study st
        WHERE st.study_specifier=%s
        ;
        ''', (self.study,))

    def drop_sample_strata(self):
        logger.info('Dropping sample_strata records.')
        self.get_cursor().execute('''
        DELETE FROM sample_strata ss
        WHERE ss.sample IN (
            SELECT scp.specimen FROM specimen_collection_process scp
            JOIN study_component sc ON sc.component_study=scp.study
            WHERE sc.primary_study=%s
        ) ;
        ''', (self.study,))

    def drop_subject(self):
        logger.info('Dropping subject records, with cascading to intervention and diagnosis.')
        self.get_cursor().execute('''
        DELETE FROM subject sj
        WHERE sj.identifier IN (
            SELECT scp.source FROM specimen_collection_process scp
            JOIN study_component sc ON sc.component_study=scp.study
            WHERE sc.primary_study=%s
        ) ;
        ''', (self.study,))

    def drop_specimen_collection_study(self):
        logger.info('Dropping specimen_collection_study, with cascading to '
                    'specimen_collection_process and histology_assessment_process.')
        self.get_cursor().execute('''
        DELETE FROM specimen_collection_study scp
        WHERE scp.name IN (
            SELECT sc.component_study FROM study_component sc
            WHERE sc.primary_study=%s
        ) ;
        ''', (self.study,))

    def drop_study_component(self):
        logger.info('Dropping study_component records.')
        self.get_cursor().execute('''
        DELETE FROM study_component sc
        WHERE sc.primary_study=%s
        ;
        ''', (self.study,))
