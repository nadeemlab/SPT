import importlib.resources

from ..standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)


def verbose_sql_execute(
    filename,
    connection,
    description: str=None,
    silent=False,
    contents=None,
    itemize=False,
    source_package: str=None,
):
    if description is None:
        description = filename
    if not contents:
        logger.info('Executing %s.', description)
        with importlib.resources.path(source_package, filename) as path:
            script = open(path).read()
    else:
        script = contents
    cursor = connection.cursor()
    if not silent and not itemize:
        logger.debug(script)

    if itemize:
        script_statements = [s + ';' for s in script.rstrip(' \n').split(';') if s != '']
        for statement in script_statements:
            logger.debug(statement)
            cursor.execute(statement)
            connection.commit()
    else:
        cursor.execute(script)
    cursor.close()
    connection.commit()
    logger.info('Done with %s.', description)
