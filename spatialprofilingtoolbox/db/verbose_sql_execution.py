"""Do execution of a SQL statement and log the activity."""
import importlib.resources
from typing import Optional
from typing import Literal

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

VerbosityOptions = Literal['itemize', 'silent', None]

def verbose_sql_execute(
    filename_description,
    connection,
    contents=None,
    verbosity: VerbosityOptions = None,
    source_package: Optional[str] = None,
):
    filename, description = filename_description
    if description is None:
        description = filename
    if not contents:
        logger.info('Executing %s.', description)
        with importlib.resources.path(source_package, filename) as path:
            with open(path, encoding='utf-8') as file:
                script = file.read()
    else:
        script = contents
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
    logger.info('Done with %s.', description)
