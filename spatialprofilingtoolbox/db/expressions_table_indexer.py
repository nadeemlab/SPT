"""Set up source specimen index on big sparse expression values table."""

from spatialprofilingtoolbox.db.database_connection import retrieve_study_names
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

class ExpressionsTableIndexer:
    """Set up source specimen index on big sparse expression values table."""

    @staticmethod
    def ensure_indexed_expressions_tables(database_config_file: str | None, study: str | None = None):
        if study is None:
            studies = retrieve_study_names(database_config_file)
        else:
            studies = [study]
        for _study in studies:
            with DBCursor(database_config_file=database_config_file, study=_study) as cursor:
                logger.info('Will create custom index for study %s.', _study)
                if not ExpressionsTableIndexer.expressions_table_is_indexed(cursor):
                    ExpressionsTableIndexer.create_index(cursor)
                else:
                    logger.debug('Expression table for "%s" is already indexed.', _study)

    @staticmethod
    def expressions_table_is_indexed(cursor):
        columns = ExpressionsTableIndexer.get_expression_quantification_columns(cursor)
        return 'source_specimen' in columns

    @staticmethod
    def get_expression_quantification_columns(cursor):
        cursor.execute('''
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'expression_quantification' ;
        ''')
        return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def create_index(cursor):
        ETI = ExpressionsTableIndexer #pylint: disable=invalid-name
        ETI.log_current_indexes(cursor)
        logger.debug('Will create extra index column "source_specimen".')
        ETI.create_extra_column(cursor)
        ETI.copy_in_source_specimen_values(cursor)
        ETI.create_index_on_new_column(cursor)

    @staticmethod
    def create_extra_column(cursor):
        message = ('Creating column specifically for index, "source_specimen" on '
                   '"expression_quantification".')
        logger.debug(message)
        cursor.execute('''
        ALTER TABLE expression_quantification
        ADD COLUMN IF NOT EXISTS source_specimen VARCHAR(512) ;
        ''')
        ExpressionsTableIndexer.log_current_columns(cursor)

    @staticmethod
    def log_current_columns(cursor):
        columns = ExpressionsTableIndexer.get_expression_quantification_columns(cursor)
        logger.debug('"expression_quantification" columns: %s', columns)

    @staticmethod
    def copy_in_source_specimen_values(cursor):
        logger.debug('Copying in the source specimen values.')
        cursor.execute('''
        UPDATE expression_quantification eq
        SET source_specimen=subquery.source_specimen
        FROM (
            SELECT
                eq2.histological_structure as histological_structure,
                eq2.target as target,
                sdmp.specimen as source_specimen
            FROM expression_quantification eq2
            JOIN histological_structure_identification hsi ON hsi.histological_structure=eq2.histological_structure
            JOIN data_file df ON hsi.data_source=df.sha256_hash
            JOIN specimen_data_measurement_process sdmp ON df.source_generation_process=sdmp.identifier
        ) AS subquery
        WHERE subquery.histological_structure=eq.histological_structure
            AND subquery.target=eq.target ;
        ''')
        ExpressionsTableIndexer.log_summary_of_index_values(cursor)

    @staticmethod
    def log_summary_of_index_values(cursor):
        logger.debug('Inserted values: ')
        cursor.execute('''
        SELECT eq.source_specimen FROM expression_quantification eq
        LIMIT 5 ;
        ''')
        first_values = [row[0] for row in cursor.fetchall()]
        for value in first_values:
            logger.debug('    %s', value)
        logger.debug('    ...')
        cursor.execute('SELECT COUNT(*) FROM expression_quantification ;')
        count = cursor.fetchall()[0][0]
        logger.debug('%s total values.', count)

    @staticmethod
    def create_index_on_new_column(cursor):
        logger.debug('Creating index on the new "source_specimen" column.')
        cursor.execute('''
        CREATE INDEX expression_source_specimen ON expression_quantification (source_specimen) ;
        ''')
        ExpressionsTableIndexer.log_current_indexes(cursor)

    @staticmethod
    def log_current_indexes(cursor):
        cursor.execute('''
        SELECT indexname, indexdef
        FROM pg_indexes WHERE tablename='expression_quantification' ;
        ''')
        rows = cursor.fetchall()
        if len(rows) == 0:
            logger.debug('No indexes on "expression_quantification".')
        else:
            logger.debug('Indexes on "expression_quantification":')
            logger.debug('    (indexname, indexdef)')
            for row in rows:
                logger.debug('    %s', row)

    @staticmethod
    def drop_index(database_config_file: str | None, study: str | None = None):
        if study is None:
            studies = retrieve_study_names(database_config_file)
        else:
            studies = [study]
        for _study in studies:
            with DBCursor(database_config_file=database_config_file, study=_study) as cursor:
                is_indexed = ExpressionsTableIndexer.expressions_table_is_indexed(cursor)
                if not is_indexed:
                    logger.debug('There is no index to drop for "%s" database.', _study)
                    continue
                logger.debug('Will drop "source_specimen" column and index in "%s" database.', _study)
                cursor.execute('''
                DROP INDEX IF EXISTS expression_source_specimen ;            
                ''')
                cursor.execute('''
                ALTER TABLE expression_quantification
                DROP COLUMN IF EXISTS source_specimen ;
                ''')
            with DBCursor(database_config_file=database_config_file, study=_study) as cursor:
                ExpressionsTableIndexer.log_current_indexes(cursor)
