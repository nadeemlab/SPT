"""Create a convenience index column on the sparse expression data table."""
import argparse
from os.path import abspath
from os.path import expanduser
import sys

from spatialprofilingtoolbox.db.expressions_table_indexer import ExpressionsTableIndexer
from spatialprofilingtoolbox import DatabaseConnectionMaker
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('index-expressions-table')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt db index-expressions-table',
        description='Create an index on the big sparse expression data table to allow more '
                    'efficient access operations.'
    )
    add_argument(parser, 'database config')
    parser.add_argument('--drop-index', dest='drop_index', action='store_true')
    args = parser.parse_args()

    logger.info('')
    logger.info('spt db index-expressions-table called.')

    database_config_file = abspath(expanduser(args.database_config_file))
    with DatabaseConnectionMaker(database_config_file) as dcm:
        connection = dcm.get_connection()
        if args.drop_index:
            STATUS = ExpressionsTableIndexer.drop_index(connection)
            if STATUS is False:
                logger.debug('Can not drop index, does not exists.')
                sys.exit(1)
        else:
            ExpressionsTableIndexer.ensure_indexed_expressions_table(connection)
