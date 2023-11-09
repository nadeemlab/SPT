"""Drop a single study."""

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class StudyDropper:
    """Drop a single study."""

    @staticmethod
    def drop(database_config_file: str | None, study: str) -> None:
        """ Use this method as the entrypoint into this class' functionality."""
        with DBCursor(database_config_file=database_config_file) as cursor:
            cursor.execute('SELECT database_name FROM study_lookup WHERE study=%s ;', (study,))
            rows = cursor.fetchall()
            if len(rows) != 1:
                logger.warning('No database found for study "%s".', study)
                return
            database_name = rows[0][0]

        with DBCursor(database_config_file=database_config_file, autocommit = False) as cursor:
            cursor.execute('DROP DATABASE %s' % database_name)

        with DBCursor(database_config_file=database_config_file) as cursor:
            cursor.execute('DELETE FROM study_lookup WHERE study=%s ;', (study,))

        logger.info('Dropped database %s.', (database_name,))
