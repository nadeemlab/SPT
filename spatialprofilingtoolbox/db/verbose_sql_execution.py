"""Do execution of a SQL statement and log the activity."""
from importlib.resources import as_file
from importlib.resources import files
from typing import Literal

from spatialprofilingtoolbox.db.database_connection import DBConnection
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

VerbosityOptions = Literal['itemize', 'silent', None]


def _retrieve_script(
    filename_description: tuple[str, str],
    contents: str | None,
    source_package: str | None,
) -> str:
    filename, description = filename_description
    if description is None:
        description = filename
    if contents is None:
        if source_package is None:
            raise ValueError('Must supply package for source SQL file.')
        logger.info('Will execute %s.', description)
        with as_file(files(source_package).joinpath(filename)) as path:
            with open(path, encoding='utf-8') as file:
                script = file.read()
    else:
        script = contents
    return script


def verbose_sql_execute(
    filename_description: tuple[str, str],
    database_config_file: str | None,
    contents: str | None = None,
    verbosity: VerbosityOptions = None,
    source_package: str | None = None,
    study: str | None = None,
):
    script = _retrieve_script(filename_description, contents, source_package)
    with DBConnection(database_config_file=database_config_file, study=study) as connection:
        cursor = connection.cursor()
        if not verbosity == 'silent':
            logger.debug(script)

        if verbosity == 'itemize':
            script_statements = [
                s + ';' for s in script.rstrip(' \n').split(';') if s != '']
            for statement in script_statements:
                logger.debug(statement)
                cursor.execute(statement)
                connection.commit()
        else:
            cursor.execute(script)
        cursor.close()
        connection.commit()
        logger.info('Done with %s.', filename_description[1])
