"""Create a convenience index column on the sparse expression data table."""
import argparse
from os.path import abspath
from os.path import expanduser

from spatialprofilingtoolbox.db.expressions_table_indexer import ExpressionsTableIndexer
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
    parser.add_argument('--study', dest='study', default=None, type=str)
    args = parser.parse_args()

    logger.info('')
    logger.info('spt db index-expressions-table called.')

    database_config_file = abspath(expanduser(args.database_config_file))
    if args.drop_index:
        ExpressionsTableIndexer.drop_index(database_config_file, study=args.study)
    else:
        ExpressionsTableIndexer.ensure_indexed_expressions_tables(database_config_file, study=args.study)
