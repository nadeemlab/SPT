import argparse
import os
from os.path import join
from os.path import exists
from os.path import abspath
from os.path import expanduser

import spatialprofilingtoolbox
from spatialprofilingtoolbox.module_load_error import SuggestExtrasException
try:
    from spatialprofilingtoolbox.workflow.environment.configuration_settings import default_db_config_filename
    from spatialprofilingtoolbox.workflow.environment.source_file_parsers.skimmer import DataSkimmer
except ModuleNotFoundError as e:
    SuggestExtrasException(e, 'db')


if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog = 'spt db create-schema',
        description = 'Create pathstudies database with defined schema.'
    )
    parser.add_argument(
        '--database-config-file',
        dest='database_config_file',
        type=str,
        required=False,
        help='Provide the file for database configuration. Default is ~/%s .' % default_db_config_filename,
    )
    parser.add_argument(
        '--force',
        dest='force',
        action='store_true',
        help='By default, tables are created only if they don\'t already exist. If "force" is set, all tables from the schema are dropped first. Obviously, use with care; all data in existing tables will be deleted.',
    )
    parser.add_argument(
        '--refresh-views-only',
        dest='refresh_views_only',
        action='store_true',
        help='Only refresh materialized views, do not touch main table schema.',
    )
    parser.add_argument(
        '--recreate-views-only',
        dest='recreate_views_only',
        action='store_true',
        help='Only recreate views, do not touch main table schema.',
    )
    args = parser.parse_args()

    if args.database_config_file:
        config_file = abspath(expanduser(args.database_config_file))
    else:
        config_file = join(expanduser('~'), default_db_config_filename)
    if not exists(config_file):
    	raise FileNotFoundError('Need to supply valid database config filename: %s', config_file)

    with DataSkimmer(database_config_file=config_file) as skimmer:
        if not args.refresh_views_only and not args.recreate_views_only:
        	skimmer.create_tables(skimmer.get_connection(), force=args.force)
        else:
            if args.refresh_views_only and args.recreate_views_only:
                print('Warning: Supply only one of --refresh-views-only or --recreate-views-only')
                exit()
            if args.refresh_views_only:
                skimmer.refresh_views(skimmer.get_connection())
            if args.recreate_views_only:
                skimmer.recreate_views(skimmer.get_connection())
