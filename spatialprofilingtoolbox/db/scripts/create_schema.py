"""
CLI utility to infuse the single-cell ADI schema into a given Postgresql
instance.
"""
import argparse

from spatialprofilingtoolbox.db.database_connection import get_and_validate_database_config
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.standalone_utilities.module_load_error import SuggestExtrasException
try:
    from spatialprofilingtoolbox.db.schema_infuser import SchemaInfuser
except ModuleNotFoundError as e:
    SuggestExtrasException(e, 'db')

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt db create-schema')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt db create-schema',
        description='Create scstudies database with defined schema.'
    )
    add_argument(parser, 'database config')
    parser.add_argument(
        '--force',
        dest='force',
        action='store_true',
        help='By default, tables are created only if they don\'t already exist. '
        'If "force" is set, all tables from the schema are dropped first. '
        'Obviously, use with care; all data in existing tables will be deleted.',
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--refresh-views-only',
        dest='refresh_views_only',
        action='store_true',
        help='Only refresh materialized views, do not touch main table schema.',
    )
    group.add_argument(
        '--recreate-views-only',
        dest='recreate_views_only',
        action='store_true',
        help='Only recreate views, do not touch main table schema.',
    )
    args = parser.parse_args()

    config_file = get_and_validate_database_config(args)
    with SchemaInfuser(database_config_file=config_file) as infuser:
        if not args.refresh_views_only and not args.recreate_views_only:
            infuser.setup_schema(force=args.force)
        else:
            if args.refresh_views_only:
                infuser.refresh_views()
            if args.recreate_views_only:
                infuser.recreate_views()
