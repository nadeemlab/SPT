"""Drop a single study."""

from psycopg.errors import InvalidCatalogName

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import DBConnection
from spatialprofilingtoolbox.db.study_tokens import StudyCollectionNaming
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class StudyDropper:
    """Drop a single study."""

    @staticmethod
    def drop(database_config_file: str | None, study: str) -> None:
        """ Use this method as the entrypoint into this class' functionality."""
        def matches_base_study(_study: str) -> bool:
            if _study == study:
                return True
            extract, _ = StudyCollectionNaming.strip_token(_study)
            if extract == study:
                return True
            return False

        with DBCursor(database_config_file=database_config_file) as cursor:
            cursor.execute('SELECT database_name, study FROM study_lookup ;')
            rows = cursor.fetchall()
            matches = tuple(filter(lambda row: matches_base_study(row[1]), rows))
            if len(matches) != 1:
                logger.warning('No database found for study "%s".', study)
                return
            database_name = matches[0][0]

        with DBConnection(database_config_file=database_config_file, autocommit = True) as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                try:
                    cursor.execute(f'DROP DATABASE {database_name} ;')
                    logger.info(f'Dropped database: {database_name}')
                except InvalidCatalogName:
                    logger.warning(f'The database {database_name} does not exist, can not drop it.')

        with DBCursor(database_config_file=database_config_file) as cursor:
            cursor.execute('DELETE FROM study_lookup WHERE database_name=%s ;', (database_name,))
            logger.info('Dropped record of database %s.', database_name)
