"""Utility to managed features computed on demand."""
import argparse

from spatialprofilingtoolbox.db.ondemand_dropper import OnDemandComputationsDropper
from spatialprofilingtoolbox.db.database_connection import get_and_validate_database_config
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.db.database_connection import DBCursor

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt db drop-ondemand-computations')

def main():
    parser = argparse.ArgumentParser(
        prog='spt db drop-ondemand-computations',
        description='Drop ondemand-computed features, including values, specifiers, etc.'
    )
    add_argument(parser, 'database config')
    add_argument(parser, 'study name')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--pending-only',
        action='store_true',
        default=False,
    )
    group.add_argument(
        '--all',
        action='store_true',
        default=False,
    )
    args = parser.parse_args()

    config_file = get_and_validate_database_config(args)
    with DBCursor(database_config_file=config_file, study=args.study_name) as cursor:
        if args.pending_only:
            OnDemandComputationsDropper.drop(cursor, pending_only=True)
        if args.all:
            OnDemandComputationsDropper.drop(cursor, drop_all=True)

if __name__ == '__main__':
    main()
